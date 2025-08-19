Tuyệt — mình đề xuất cách làm “ít đụng chạm” nhất vào code sẵn có của bạn:

* **Dán code adapter + orchestrator vào `data_models.py`** (để chuyển JSON filter do LLM sinh thành `arguments.filters` đúng schema MCP, rồi chạy Discovery → Targeted).
* **Không cần sửa `shopify_api_client.py`** vì file này đã hỗ trợ truyền `filters` vào body JSON‑RPC rồi (hàm `search_products(...)` → `_create_search_request(...)` sẽ tự thêm `arguments.filters` nếu bạn truyền vào).

Dưới đây là:

1. Quy trình chuẩn (chuỗi thao tác end‑to‑end)
2. Code bạn dán thẳng vào **cuối file `data_models.py`**
3. Ví dụ gọi thực tế (dán vào nơi bạn đang xử lý input của LLM)

---

# 1) Quy trình chuẩn (chuỗi thao tác)

1. **LLM** nhận input tự nhiên → sinh ra **JSON filter** (keywords, productType, colors, materials, price…).
2. **Discovery search** (không filter) bằng từ khóa danh mục (ví dụ: “dresses”) để lấy `available_filters` do shop **thực sự** hỗ trợ.
3. **Adapter**: Từ JSON filter của LLM → map sang mảng `filters` đúng **MCP schema** (chỉ giữ những filter xuất hiện trong `available_filters`, ví dụ `productType`, `variantOption` cho Color/Size, `price`, `tag`, `productMetafield`/`variantMetafield`…).
4. **Targeted search**: gọi lại API với `query` sạch + `filters` đã map để lấy đúng kết quả.
5. (Tuỳ chọn) Phân trang / lọc lại / hiển thị.

> Lưu ý: `shopify_api_client.search_products(query, context, limit, filters)` đã hỗ trợ truyền `filters` và nó sẽ tự nhét vào body JSON‑RPC (`arguments.filters`). Bạn không phải thao tác body JSON‑RPC thủ công nữa.

---

# 2) Dán code vào **cuối file `data_models.py`**

> Code này gồm:
>
> * Parser `extract_available_filters(...)` để đọc `available_filters` trả về từ Discovery
> * Adapter `llm_to_mcp_filters(...)` để map JSON filter của LLM → MCP filters
> * Orchestrator `search_with_llm_filters(...)` để chạy Discovery → Targeted bằng `ShopifyAPIClient`

```python
# =========================
# Append to: data_models.py
# =========================
from typing import Any, Dict, List, Tuple, Optional
import re

# ---- 1) Helpers: đọc available_filters từ response JSON của MCP ----

def _safe_get_available_filters(api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Trả về mảng available_filters từ JSON trả về của MCP.
    Cấu trúc điển hình:
      result -> content[0] -> type="text" -> text (string JSON) -> { "available_filters": [...] }
    hoặc đôi khi trả thẳng {"available_filters": [...]} trong text.
    """
    try:
        result = api_response.get("result", {}) or api_response.get("data", {})
        contents = result.get("content", [])
        for item in contents:
            if item.get("type") == "text" and "text" in item:
                import json
                as_json = json.loads(item["text"])
                if isinstance(as_json, dict) and "available_filters" in as_json:
                    return as_json["available_filters"] or []
        # Fallback nếu cấu trúc khác
        return []
    except Exception:
        return []


def extract_available_filters(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuẩn hoá available_filters thành dict dễ dùng:
    {
      "supports": {
         "productType": bool,
         "price": bool,
         "available": bool,
         "tag": bool,
         "variantOption": {"Color": True, "Size": True, ...},
         "productMetafield": [{"namespace":"specs","key":"material"}, ...]   # nếu phát hiện được
      },
      "raw": [...]   # dữ liệu gốc để debug
    }
    """
    afs = _safe_get_available_filters(api_response)
    supports = {
        "productType": False,
        "price": False,
        "available": False,
        "tag": False,
        "variantOption": {},   # map tên option -> True
        "productMetafield": [] # list {namespace,key}
    }

    # Dò theo pattern chung: mỗi filter có "label" + "values.input_options[*].input"
    for f in afs:
        label = (f.get("label") or "").strip().lower()
        values = f.get("values", {}) or {}
        input_opts = values.get("input_options", []) or []

        # Kiểm tra xem trong input có field nào của MCP schema
        for opt in input_opts:
            inp = opt.get("input", {})
            if "productType" in inp:
                supports["productType"] = True
            if "price" in inp:
                supports["price"] = True
            if "available" in inp:
                supports["available"] = True
            if "tag" in inp:
                supports["tag"] = True
            if "variantOption" in inp:
                vo = inp["variantOption"]
                name = (vo.get("name") or "").strip()
                if name:
                    supports["variantOption"][name] = True
            # Metafield (tuỳ shop có expose hay không)
            if "productMetafield" in inp:
                pm = inp["productMetafield"]
                nk = {"namespace": pm.get("namespace"), "key": pm.get("key")}
                if nk not in supports["productMetafield"]:
                    supports["productMetafield"].append(nk)

    return {"supports": supports, "raw": afs}


# ---- 2) Adapter: LLM JSON -> MCP filters (dựa trên supports từ Discovery) ----

def _normalize_title(s: str) -> str:
    return (s or "").strip().title()

def _normalize_upper(s: str) -> str:
    return (s or "").strip().upper()

def llm_to_mcp_filters(llm_filters: Dict[str, Any], available_filter_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Map JSON filter sinh bởi LLM sang mảng MCP filters hợp lệ,
    chỉ giữ những filter có trong available_filters của shop.
    """
    out: List[Dict[str, Any]] = []
    supports = (available_filter_info or {}).get("supports", {})

    # 1) productType
    if "productType" in llm_filters and supports.get("productType"):
        out.append({"productType": _normalize_title(llm_filters["productType"])})

    # 2) colors -> variantOption: {name: "Color", value: "Red"}
    if "colors" in llm_filters and isinstance(llm_filters["colors"], list):
        if supports.get("variantOption", {}).get("Color"):
            for c in llm_filters["colors"]:
                out.append({"variantOption": {"name": "Color", "value": _normalize_title(c)}})

    # 3) sizes -> variantOption: {name: "Size", value: "M"} (nếu có)
    if "sizes" in llm_filters and isinstance(llm_filters["sizes"], list):
        if supports.get("variantOption", {}).get("Size"):
            for s in llm_filters["sizes"]:
                out.append({"variantOption": {"name": "Size", "value": _normalize_upper(s)}})

    # 4) materials -> nếu shop expose productMetafield tương ứng (ví dụ namespace/specs, key/material)
    if "materials" in llm_filters and isinstance(llm_filters["materials"], list):
        pm_list = supports.get("productMetafield", []) or []
        # Tìm metafield có vẻ là "material"
        material_meta = None
        for item in pm_list:
            if (item.get("key") or "").lower() == "material":
                material_meta = item
                break
        if material_meta:
            ns = material_meta.get("namespace") or "specs"
            key = material_meta.get("key") or "material"
            for m in llm_filters["materials"]:
                out.append({"productMetafield": {"namespace": ns, "key": key, "value": m}})

    # 5) price {min,max} hoặc {max}
    price_obj = llm_filters.get("price")
    if supports.get("price") and isinstance(price_obj, dict):
        min_v = float(price_obj.get("min", 0)) if price_obj.get("min") is not None else 0.0
        max_v = price_obj.get("max")
        if max_v is not None:
            out.append({"price": {"min": float(min_v), "max": float(max_v)}})
        # Nếu shop chỉ expose price range cố định, có thể cần clamp theo available_filters; ở đây để đơn giản bỏ qua.

    # 6) sales/tags -> tag
    if "sales" in llm_filters and supports.get("tag"):
        # ví dụ: ["sale"] hoặc ["final-sale"]
        for tag in llm_filters["sales"]:
            out.append({"tag": str(tag)})

    # 7) availability
    if "available" in llm_filters and supports.get("available"):
        out.append({"available": bool(llm_filters["available"])})

    return out


# ---- 3) Orchestrator: Discovery -> Targeted ----

def _pick_discovery_query(llm_json: Dict[str, Any]) -> str:
    # Ưu tiên productType; nếu không có, dùng từ đầu trong keywords; fallback "products"
    f = (llm_json.get("filters") or {})
    if f.get("productType"):
        return str(f["productType"])
    kws = llm_json.get("keywords") or []
    if isinstance(kws, list) and len(kws) > 0:
        return str(kws[0])
    # Fallback
    return "products"

def _pick_target_query(llm_json: Dict[str, Any]) -> str:
    return llm_json.get("clean_query") or " ".join(llm_json.get("keywords", [])) or "products"

def search_with_llm_filters(
    client,               # ShopifyAPIClient
    llm_json: Dict[str, Any],
    discovery_limit: int = 5,
    targeted_limit: int = 10,
    context_prefix: str = "intelligent search"
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Chạy đầy đủ: Discovery -> Adapter -> Targeted.
    Trả về (discovery_response_json, targeted_response_json, used_filters)
    """
    # 1) Discovery
    discovery_query = _pick_discovery_query(llm_json)
    disc_res = client.search_products(
        query=discovery_query,
        context=f"{context_prefix} - discovery search to list available filters for {discovery_query}",
        limit=discovery_limit
    )
    if not getattr(disc_res, "success", False):
        # Trả ngay nếu Discovery lỗi
        return disc_res.__dict__, {}, []

    disc_json = disc_res.data if isinstance(disc_res.data, dict) else disc_res.data
    af_info = extract_available_filters(disc_json)

    # 2) Adapter
    mcp_filters = llm_to_mcp_filters(llm_json.get("filters", {}), af_info)

    # 3) Targeted
    target_query = _pick_target_query(llm_json)
    targ_res = client.search_products(
        query=target_query,
        context=f"{context_prefix} - targeted search generated from LLM filters",
        limit=targeted_limit,
        filters=mcp_filters if mcp_filters else None
    )
    return disc_res.data, (targ_res.data if getattr(targ_res, "success", False) else targ_res.__dict__), mcp_filters
```

---

# 3) Cách gọi thực tế (ví dụ tích hợp)

> Ví dụ bên dưới dán vào phần bạn đang xử lý pipeline (controller/service).
> Giả sử bạn đã có `ShopifyAPIClient` tên `client` (khởi tạo với `base_url`, headers…).

```python
from shopify_api_client import ShopifyAPIClient
from data_models import search_with_llm_filters

# Khởi tạo client (ví dụ)
config = {
    "api": {
        "base_url": "https://gravio-bao-m4.myshopify.com/api/mcp",
        "timeout": 30,
        "retries": 3,
        "headers": {"Content-Type": "application/json"}
    }
}
client = ShopifyAPIClient(config)

# JSON filter do LLM sinh (ví dụ user trước đó)
llm_json = {
    "keywords": ["red", "cotton", "dresses"],
    "filters": {
        "colors": ["red"],
        "materials": ["cotton"],
        "productType": "dresses"
    },
    "clean_query": "red cotton dresses",
    "confidence": 0.95
}

discovery_json, targeted_json, used_filters = search_with_llm_filters(
    client=client,
    llm_json=llm_json,
    discovery_limit=5,
    targeted_limit=10,
    context_prefix="intelligent search"
)

# -> Bạn có thể log 3 biến này để kiểm tra:
#    - discovery_json: response chứa available_filters
#    - used_filters: mảng MCP filters đã map (chỉ dùng filter hợp lệ)
#    - targeted_json: kết quả cuối cùng (sản phẩm)
```

---

## Tại sao dán vào `data_models.py`?

* File **`shopify_api_client.py`** đã “chuẩn” để gửi request JSON‑RPC (POST) với khả năng đính kèm `filters` ngay khi bạn truyền vào `search_products(...)`. Cụ thể, `_create_search_request(...)` tự thêm `arguments.filters` khi `filters` khác `None` → không cần sửa file này.
* Phần “dịch” JSON của LLM → MCP filters (và pipeline Discovery → Targeted) hợp lý nhất là nằm ở **tầng model/adapter** (ở đây là `data_models.py`) để giữ client “mỏng” và tái sử dụng được ở nhiều nơi.

Nếu bạn muốn tách gọn hơn, mình có thể tách phần adapter thành file riêng `adapters/mcp_filter_adapter.py` và ở `data_models.py` chỉ import dùng — nhưng để đơn giản thì dán trực tiếp như trên là chạy được ngay.
