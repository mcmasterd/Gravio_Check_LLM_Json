# Shopify MCP Tools - Detailed Guide

This document contains details of all Shopify MCP tools with real curl examples.

## 🧠 **INTELLIGENT SEARCH STRATEGY WITH MCP**

### **🎯 Observed issue from logs:**
- **Query:** "Show me mini-skirts under 500 dollars"  
- **Result:** `"products":[]` - No results
- **Cause:** MCP requires explicit filters and does not understand complex queries directly

### **✅ SOLUTION: 2-STEP INTELLIGENT SEARCH**

#### **Step 1: Discovery Search (find available filters)**
```bash
curl -X POST https://gravio-bao-m4.myshopify.com/api/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0", 
  "method": "tools/call", 
  "id": 1,
  "params": {
    "name": "search_shop_catalog",
    "arguments": {
      "query": "skirts",
      "context": "discovery search to find available filters",
      "limit": 5
    }
  }
}'
```

**Response includes `available_filters`:**
```json
{
  "available_filters": [
    {
      "label": "Price",
      "values": {
        "input_options": [
          {
            "label": "Price",
            "input": {"price": {"min": 0, "max": 500.0}}
          }
        ]
      }
    },
    {
      "label": "Product Type", 
      "values": {
        "input_options": [
          {
            "label": "Skirts",
            "input": {"productType": "Skirts"}
          }
        ]
      }
    }
  ]
}
```

#### **Step 2: Targeted Search (search with filters)**
```bash
curl -X POST https://gravio-bao-m4.myshopify.com/api/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "method": "tools/call", 
  "id": 1,
  "params": {
    "name": "search_shop_catalog",
    "arguments": {
      "query": "mini skirts",
      "context": "targeted search with price filter",
      "filters": [
        {
          "price": {
            "min": 0,
            "max": 500
          }
        },
        {
          "productType": "Skirts"
        }
      ],
      "limit": 10
    }
  }
}'
```

### **🛠️ IMPLEMENTATION PATTERNS FOR CHATBOT:**

#### **Pattern 1: Price Range Queries**
```javascript
// Input: "products under $500"
// Processed query: 
{
  "query": "products",
  "filters": [
    {
      "price": {
        "min": 0,
        "max": 500
      }
    }
  ]
}
```

#### **Pattern 2: Category + Price Queries**  
```javascript
// Input: "polo shirts under $100"
// Processed query:
{
  "query": "polo shirts", 
  "filters": [
    {
      "price": {
        "min": 0,
        "max": 100
      }
    },
    {
      "productType": "Polos & Dress Shirts"
    }
  ]
}
```

#### **Pattern 3: Color/Size Specific Queries**
```javascript
// Input: "red polo shirt size M"
// Processed query:
{
  "query": "polo shirt",
  "filters": [
    {
      "variantOption": {
        "name": "Color",
        "value": "Red"
      }
    },
    {
      "variantOption": {
        "name": "Size", 
        "value": "M"
      }
    }
  ]
}
```

### **🧠 INTELLIGENT QUERY PARSING LOGIC:**

#### **Price Extraction Patterns:**
```javascript
const pricePatterns = [
  /under\s*\$?(\d+)/i,           // "under $500"
  /below\s*\$?(\d+)/i,          // "below $300"
  /less than\s*\$?(\d+)/i,      // "less than $200"
  /cheaper than\s*\$?(\d+)/i,   // "cheaper than $150"
  /\$?(\d+)\s*or less/i,        // "$100 or less"
  /maximum\s*\$?(\d+)/i,        // "maximum $400"
  /max\s*\$?(\d+)/i             // "max $250"
];

function extractPriceFilter(query) {
  for (const pattern of pricePatterns) {
    const match = query.match(pattern);
    if (match) {
      return {
        price: {
          min: 0,
          max: parseFloat(match[1])
        }
      };
    }
  }
  return null;
}
```

#### **Product Type Extraction:**
```javascript
const productTypeMap = {
  'polo': 'Polos & Dress Shirts',
  'shirt': 'Polos & Dress Shirts', 
  'skirt': 'Skirts',
  'dress': 'Dresses',
  'jacket': 'Jackets',
  'accessory': 'Accessories'
};

function extractProductTypeFilter(query) {
  for (const [keyword, productType] of Object.entries(productTypeMap)) {
    if (query.toLowerCase().includes(keyword)) {
      return {
        productType: productType
      };
    }
  }
  return null;
}
```

#### **Color/Size Extraction:**
```javascript
const colors = ['red', 'blue', 'green', 'black', 'white', 'navy', 'gray'];
const sizes = ['xs', 's', 'm', 'l', 'xl', 'xxl'];

function extractVariantFilters(query) {
  const filters = [];
  
  // Extract color
  const colorMatch = colors.find(color => 
    query.toLowerCase().includes(color)
  );
  if (colorMatch) {
    filters.push({
      variantOption: {
        name: "Color",
        value: colorMatch.charAt(0).toUpperCase() + colorMatch.slice(1)
      }
    });
  }
  
  // Extract size
  const sizeMatch = sizes.find(size =>
    new RegExp(`\\bsize\\s+${size}\\b|\\b${size}\\s+size\\b`, 'i').test(query)
  );
  if (sizeMatch) {
    filters.push({
      variantOption: {
        name: "Size",
        value: sizeMatch.toUpperCase()
      }
    });
  }
  
  return filters;
}
```

### **📋 COMPLETE IMPLEMENTATION EXAMPLE:**

```javascript
async function intelligentProductSearch(userQuery, context = "intelligent search") {
  // Step 1: Parse query for filters
  const priceFilter = extractPriceFilter(userQuery);
  const productTypeFilter = extractProductTypeFilter(userQuery); 
  const variantFilters = extractVariantFilters(userQuery);
  
  // Step 2: Clean query (remove price/filter terms)
  let cleanQuery = userQuery
    .replace(/under\s*\$?\d+/gi, '')
    .replace(/below\s*\$?\d+/gi, '')
    .replace(/size\s+[a-z]+/gi, '')
    .replace(/\b(red|blue|green|black|white)\b/gi, '')
    .trim();
  
  // Step 3: Build filters array
  const filters = [];
  if (priceFilter) filters.push(priceFilter);
  if (productTypeFilter) filters.push(productTypeFilter);
  filters.push(...variantFilters);
  
  // Step 4: Execute search
  const searchParams = {
    query: cleanQuery,
    context: context,
    limit: 10
  };
  
  if (filters.length > 0) {
    searchParams.filters = filters;
  }
  
  console.log(`🧠 [INTELLIGENT-SEARCH] Original: "${userQuery}"`);
  console.log(`🧠 [INTELLIGENT-SEARCH] Clean query: "${cleanQuery}"`);
  console.log(`🧠 [INTELLIGENT-SEARCH] Filters:`, filters);
  
  return await mcpClient.callTool('search_shop_catalog', searchParams);
}
```

### **🎯 KEY BENEFITS:**

1. **🎯 Precise Results:** Filters eliminate irrelevant products
2. **💰 Price Awareness:** Automatic price range filtering  
3. **🎨 Style Matching:** Color/size variant filtering
4. **📦 Category Focus:** Product type filtering
5. **🚀 Better UX:** Users get exactly what they ask for

### **⚠️ IMPORTANT NOTES:**

- **ALWAYS** use `available_filters` from discovery search
- **NEVER** hardcode filter values - extract from actual API response
- **COMBINE** multiple filters for complex queries
- **FALLBACK** to simple search if filters fail

---

## 1. LIST ALL TOOLS

### Curl Command:
```bash
curl -X POST https://gravio-bao-m4.myshopify.com/api/mcp -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1, "params": {}}'
```

### Actual response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "search_shop_catalog",
        "description": "Search for products from the online store, hosted on Shopify.\n\nThis tool can be used to search for products using natural language queries, specific filter criteria, or both.\n\nBest practices:\n- Searches return available_filters which can be used for refined follow-up searches\n- When filtering, use ONLY the filters from available_filters in follow-up searches\n- For specific filter searches (category, variant option, product type, etc.), use simple terms without the filter name (e.g., \"red\" not \"red color\")\n- For filter-specific searches (e.g., \"find burton in snowboards\" or \"show me all available products in gray / green color\"), use a two-step approach:\n  1. Perform a normal search to discover available filters\n  2. If relevant filters are returned, do a second search using the proper filter (productType, category, variantOption, etc.) with just the specific search term\n- Results are paginated, with initial results limited to improve experience\n- Use the after parameter with endCursor to fetch additional pages when users request more results\n\nThe response includes product details, available variants, filter options, and pagination info.\n",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "A natural language query."
            },
            "filters": {
              "type": "array",
              "description": "Filters to apply to the search. Only apply filters from the available_filters returned in a previous response.",
              "items": {
                "type": "object",
                "properties": {
                  "available": {
                    "type": "boolean",
                    "description": "Filter on if the product is available for sale",
                    "default": true
                  },
                  "category": {
                    "type": "object",
                    "description": "Category ID to filter by",
                    "properties": {
                      "id": {
                        "type": "string",
                        "description": "Category ID to filter by"
                      }
                    }
                  },
                  "price": {
                    "type": "object",
                    "description": "Price range to filter by",
                    "properties": {
                      "min": {
                        "type": "number",
                        "description": "Minimum price to filter by, represented as a float, e.g. 50.0"
                      },
                      "max": {
                        "type": "number",
                        "description": "Maximum price to filter by, represented as a float, e.g. 100.0"
                      }
                    }
                  },
                  "productMetafield": {
                    "type": "object",
                    "description": "Filter on a product metafield",
                    "properties": {
                      "key": {
                        "type": "string",
                        "description": "The key of the metafield to filter by"
                      },
                      "namespace": {
                        "type": "string",
                        "description": "The namespace of the metafield to filter by"
                      },
                      "value": {
                        "type": "string",
                        "description": "The value of the metafield to filter by"
                      }
                    }
                  },
                  "productType": {
                    "type": "string",
                    "description": "Product type to filter by"
                  },
                  "productVendor": {
                    "type": "string",
                    "description": "Product vendor to filter by"
                  },
                  "tag": {
                    "type": "string",
                    "description": "Tag to filter by"
                  },
                  "taxonomyMetafield": {
                    "type": "object",
                    "description": "Taxonomy metafield to filter by",
                    "properties": {
                      "key": {
                        "type": "string"
                      },
                      "namespace": {
                        "type": "string"
                      },
                      "value": {
                        "type": "string"
                      }
                    }
                  },
                  "variantMetafield": {
                    "type": "object",
                    "description": "Variant metafield to filter by",
                    "properties": {
                      "key": {
                        "type": "string",
                        "description": "The key of the metafield to filter by"
                      },
                      "namespace": {
                        "type": "string",
                        "description": "The namespace of the metafield to filter by"
                      },
                      "value": {
                        "type": "string",
                        "description": "The value of the metafield to filter by"
                      }
                    }
                  },
                  "variantOption": {
                    "type": "object",
                    "description": "Variant option to filter by",
                    "properties": {
                      "name": {
                        "type": "string",
                        "description": "Name of the variant option to filter by"
                      },
                      "value": {
                        "type": "string",
                        "description": "Value of the variant option to filter by"
                      }
                    }
                  }
                }
              }
            },
            "country": {
              "type": "string",
              "description": "ISO 3166-1 alpha-2 country code for which to return localized results (e.g., 'US', 'CA', 'GB')."
            },
            "language": {
              "type": "string",
              "description": "ISO 639-1 language code for which to return localized results (e.g., 'EN', 'FR', 'DE')."
            },
            "limit": {
              "type": "integer",
              "description": "Maximum number of products to return. Defaults to 10, maximum is 250. For better user experience, use the default of 10 and ask the user if they want to see more results.",
              "default": 10
            },
            "after": {
              "type": "string",
              "description": "Pagination cursor to fetch the next page of results. Use the endCursor from the previous response. Only use this when the user explicitly asks to see more results."
            },
            "context": {
              "type": "string",
              "description": "Additional information about the request such as user demographics, mood, location, or other relevant details that could help in tailoring the response appropriately."
            }
          },
          "required": [
            "query",
            "context"
          ]
        }
      },
      {
        "name": "get_cart",
        "description": "Get the cart including items, shipping options, discount info, and checkout url for a given cart id",
        "inputSchema": {
          "type": "object",
          "properties": {
            "cart_id": {
              "type": "string",
              "description": "Shopify cart id, formatted like: gid://shopify/Cart/c1-66330c6d752c2b242bb8487474949791?key=fa8913e951098d30d68033cf6b7b50f3"
            }
          },
          "required": [
            "cart_id"
          ]
        }
      },
      {
        "name": "update_cart",
        "description": "Perform updates to a cart, including adding/removing/updating line items, buyer information, shipping details, discount codes, gift cards and notes in one consolidated call. Shipping options become available after adding items and delivery address. When creating a new cart, only addItems is required.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "cart_id": {
              "type": "string",
              "description": "Identifier for the cart being updated. If not provided, a new cart will be created."
            },
            "add_items": {
              "type": "array",
              "description": "Items to add to the cart. Required when creating a new cart.",
              "items": {
                "type": "object",
                "required": [
                  "product_variant_id",
                  "quantity"
                ],
                "properties": {
                  "product_variant_id": {
                    "type": "string"
                  },
                  "quantity": {
                    "type": "integer",
                    "minimum": 1
                  }
                }
              }
            },
            "update_items": {
              "type": "array",
              "description": "Existing cart line items to update quantities for. Use quantity 0 to remove an item.",
              "items": {
                "type": "object",
                "required": [
                  "id",
                  "quantity"
                ],
                "properties": {
                  "id": {
                    "type": "string"
                  },
                  "quantity": {
                    "type": "integer",
                    "minimum": 0
                  }
                }
              }
            },
            "remove_line_ids": {
              "type": "array",
              "description": "List of line item IDs to remove explicitly.",
              "items": {
                "type": "string"
              }
            },
            "buyer_identity": {
              "type": "object",
              "description": "Information about the buyer including email, phone, and delivery address.",
              "additional_properties": false,
              "properties": {
                "email": {
                  "type": "string",
                  "format": "email"
                },
                "phone": {
                  "type": "string"
                },
                "country_code": {
                  "type": "string",
                  "description": "ISO country code, used for regional pricing."
                }
              }
            },
            "delivery_addresses_to_add": {
              "type": "array",
              "description": "Information about the delivery addresses to add.",
              "items": {
                "type": "object",
                "properties": {
                  "delivery_address": {
                    "type": "object",
                    "properties": {
                      "first_name": {
                        "type": "string"
                      },
                      "last_name": {
                        "type": "string"
                      },
                      "address1": {
                        "type": "string"
                      },
                      "address2": {
                        "type": "string"
                      },
                      "city": {
                        "type": "string"
                      },
                      "province_code": {
                        "type": "string"
                      },
                      "zip": {
                        "type": "string"
                      },
                      "country_code": {
                        "type": "string",
                        "description": "ISO country code, used for regional pricing."
                      }
                    }
                  }
                }
              }
            },
            "selected_delivery_options": {
              "type": "array",
              "description": "The delivery options to select for the cart.",
              "items": {
                "type": "object",
                "properties": {
                  "group_id": {
                    "type": "string",
                    "description": "The ID of the delivery group to select."
                  },
                  "option_handle": {
                    "type": "string",
                    "description": "The handle of the delivery option to select."
                  }
                }
              }
            },
            "discount_codes": {
              "type": "array",
              "description": "Discount or promo codes to apply to the cart. Only prompt if customer mentions having a discount code.",
              "items": {
                "type": "string"
              }
            },
            "gift_card_codes": {
              "type": "array",
              "description": "Gift card codes to apply to the cart. Only prompt if customer mentions having a gift card.",
              "items": {
                "type": "string"
              }
            },
            "note": {
              "type": "string",
              "description": "A note or special instructions for the cart. Optional - can ask if customer wants to add special instructions."
            }
          },
          "required": []
        }
      },
      {
        "name": "search_shop_policies_and_faqs",
        "description": "Used to get facts about the stores policies, products, or services.\nSome examples of questions you can ask are:\n  - What is your return policy?\n  - What is your shipping policy?\n  - What is your phone number?\n  - What are your hours of operation?\"\n",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "A natural language query."
            },
            "context": {
              "type": "string",
              "description": "Additional information about the request such as user demographics, mood, location, or other relevant details that could help in tailoring the response appropriately."
            }
          },
          "required": [
            "query"
          ]
        }
      },
      {
        "name": "get_product_details",
        "description": "Look up a product by ID and optionally specify variant options to select a specific variant.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "product_id": {
              "type": "string",
              "description": "The product ID, e.g. gid://shopify/Product/123"
            },
            "options": {
              "type": "object",
              "description": "Optional variant options to select a specific variant, e.g. {\"Size\": \"10\", \"Color\": \"Black\"}"
            }
          },
          "required": [
            "product_id"
          ]
        }
      }
    ]
  }
}
```

## 2. SEARCH_SHOP_CATALOG - Product search

The most powerful tool to search for products using natural language with filters.

### Example 1: Basic search
```bash
curl -X POST https://gravio-bao-m4.myshopify.com/api/mcp -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "tools/call", "id": 1, "params": {"name": "search_shop_catalog", "arguments": {"query": "polo shirt", "context": "Customer looking for polo shirts", "limit": 3}}}'
```

### Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"products\":[{\"product_id\":\"gid://shopify/Product/7462475989082\",\"title\":\"Fun Shirt\",\"description\":\"Product Details A loving homage to the original, authentic "Fun Shirt" featuring an embroidered crowned heart motif on the lower left torso.Soft S-roll button-down collar. Pure cotton buttons. American placket. 100% cotton.Care Instructions: Dry clean only. Size \\u0026 Fit Unisex (men's sizing). This Oxford has a slim, tailored fit through the body; for a roomier fit, we recommend sizing up. For specific measurements, refer to the size chart.Cami is 5'11\\\" with a 26\\\" waist and wearing a size M.\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT_fafd0232-1ff6-4eb6-8990-c45ccb20e466.jpg?v=1746847706\",\"price_range\":{\"min\":\"118.0\",\"max\":\"118.0\",\"currency\":\"VND\"},\"product_type\":\"Polos \\u0026 Dress Shirts\",\"tags\":[\"All Tops\",\"Dress Shirts\",\"Final Sale\",\"Heart Icon\",\"July24\",\"New\",\"RB Brand\",\"Shop All\",\"summer24\"],\"variants\":[{\"variant_id\":\"gid://shopify/ProductVariant/41912399986778\",\"title\":\"Fun Shirt Multi-Stripe / XS\",\"price\":\"118.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT_fafd0232-1ff6-4eb6-8990-c45ccb20e466.jpg?v=1746847706\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912400019546\",\"title\":\"Fun Shirt Multi-Stripe / S\",\"price\":\"118.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT_fafd0232-1ff6-4eb6-8990-c45ccb20e466.jpg?v=1746847706\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912400052314\",\"title\":\"Fun Shirt Multi-Stripe / M\",\"price\":\"118.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT_fafd0232-1ff6-4eb6-8990-c45ccb20e466.jpg?v=1746847706\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912400085082\",\"title\":\"Fun Shirt Multi-Stripe / L\",\"price\":\"118.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT_fafd0232-1ff6-4eb6-8990-c45ccb20e466.jpg?v=1746847706\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912400117850\",\"title\":\"Fun Shirt Multi-Stripe / XL\",\"price\":\"118.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT_fafd0232-1ff6-4eb6-8990-c45ccb20e466.jpg?v=1746847706\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912400150618\",\"title\":\"Fun Shirt Multi-Stripe / XXL\",\"price\":\"118.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT_fafd0232-1ff6-4eb6-8990-c45ccb20e466.jpg?v=1746847706\",\"available\":true}]},{\"product_id\":\"gid://shopify/Product/7462477135962\",\"title\":\"Heart Icon Piqué Polo\",\"description\":\"Product Details FINAL SALE. Cotton piqué polo jersey featuring an embroidered crowned heart motif on the left chest.Two-button placket. Pressed cotton buttons. Flat-knit rib collar and 1x1 ribbed armbands. Split hems. 100% cotton. Knit in the highest quality piqué.Care Instructions: Machine wash cold. Do not tumble dry. Wash inside-out. Size \\u0026 Fit Unisex. This polo fits true-to-size (men's sizing). For specific measurements, refer to the size chart. Provenance "We're known for our fast-paced drops and collaborations, but for a long time, we've wanted to offer more bread-and-butter products — really well-made, versatile staples that speak for themselves and can be part of someone's everyday 'uniform',", explains Rowing Blazers Creative Director and founder Jack Carlson. "Over the past several years, we've resurrected the rugby shirt, made it relevant again, and now we're doing the same thing with our polos."\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241538_653e240c-e608-4083-99c9-18522c7e7d43.jpg?v=1746847909\",\"price_range\":{\"min\":\"84.0\",\"max\":\"84.0\",\"currency\":\"VND\"},\"product_type\":\"Polos \\u0026 Dress Shirts\",\"tags\":[\"All Tops\",\"final-sale\",\"Heart Icon\",\"July24\",\"New\",\"Polos\",\"RB Brand\",\"Shop All\",\"summer24\"],\"variants\":[{\"variant_id\":\"gid://shopify/ProductVariant/41912405262426\",\"title\":\"Light Blue / XS\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241538_653e240c-e608-4083-99c9-18522c7e7d43.jpg?v=1746847909\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912405295194\",\"title\":\"Light Blue / S\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241538_653e240c-e608-4083-99c9-18522c7e7d43.jpg?v=1746847909\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912405327962\",\"title\":\"Light Blue / M\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241538_653e240c-e608-4083-99c9-18522c7e7d43.jpg?v=1746847909\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912405360730\",\"title\":\"Light Blue / L\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241538_653e240c-e608-4083-99c9-18522c7e7d43.jpg?v=1746847909\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912405393498\",\"title\":\"Light Blue / XL\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241538_653e240c-e608-4083-99c9-18522c7e7d43.jpg?v=1746847909\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912405426266\",\"title\":\"Light Blue / XXL\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241538_653e240c-e608-4083-99c9-18522c7e7d43.jpg?v=1746847909\",\"available\":true}]},{\"product_id\":\"gid://shopify/Product/7462477070426\",\"title\":\"Heart Icon Piqué Polo\",\"description\":\"Product Details FINAL SALE. Cotton piqué polo jersey featuring an embroidered crowned heart motif on the left chest.Two-button placket. Pressed cotton buttons. Flat-knit rib collar and 1x1 ribbed armbands. Split hems. 100% cotton. Knit in the highest quality piqué.Care Instructions: Machine wash cold. Do not tumble dry. Wash inside-out. Size \\u0026 Fit Unisex. This polo fits true-to-size (men's sizing). For specific measurements, refer to the size chart.Zach is 6'0\\\" with a 32\\\" waist and wearing a size M. Provenance "We're known for our fast-paced drops and collaborations, but for a long time, we've wanted to offer more bread-and-butter products — really well-made, versatile staples that speak for themselves and can be part of someone's everyday 'uniform',", explains Rowing Blazers Creative Director and founder Jack Carlson. "Over the past several years, we've resurrected the rugby shirt, made it relevant again, and now we're doing the same thing with our polos."\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"price_range\":{\"min\":\"84.0\",\"max\":\"84.0\",\"currency\":\"VND\"},\"product_type\":\"Polos \\u0026 Dress Shirts\",\"tags\":[\"All Tops\",\"final-sale\",\"Heart Icon\",\"July24\",\"New\",\"Polos\",\"RB Brand\",\"Shop All\",\"summer24\",\"v25\"],\"variants\":[{\"variant_id\":\"gid://shopify/ProductVariant/41912404639834\",\"title\":\"White / XS\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912404672602\",\"title\":\"White / S\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912404705370\",\"title\":\"White / M\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912404738138\",\"title\":\"White / L\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912404770906\",\"title\":\"White / XL\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"available\":true},{\"variant_id\":\"gid://shopify/ProductVariant/41912404803674\",\"title\":\"White / XXL\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"available\":true}]}],\"pagination\":{\"hasNextPage\":true,\"hasPreviousPage\":false,\"startCursor\":\"eyJwYWdlIjoxLCJsYXN0X2lkIjo3NDYyNDc1OTg5MDgyLCJyZXZlcnNlIjp0cnVlfQ==\",\"endCursor\":\"eyJwYWdlIjoyLCJsYXN0X2lkIjo3NDYyNDc3MDcwNDI2LCJyZXZlcnNlIjp0cnVlfQ==\",\"currentPage\":1,\"nextPage\":2,\"maxPages\":8334,\"limitReached\":false},\"available_filters\":[{\"label\":\"Availability\",\"values\":{\"label\":[\"In stock\",\"Out of stock\"],\"input_options\":[{\"label\":\"In stock\",\"input\":{\"available\":true}},{\"label\":\"Out of stock\",\"input\":{\"available\":false}}]}},{\"label\":\"Price\",\"values\":{\"label\":[\"Price\"],\"input_options\":[{\"label\":\"Price\",\"input\":{\"price\":{\"min\":0,\"max\":268.0}}}]}}],\"instructions\":\"Use markdown to render product titles as links to their respective product pages using the URL property.\\n\\nFor product data:\\n- If variants are included in the response, those are the only variants available\\n- If variants are not included, use the options and availability matrix with get_product_details tool\\n- Check product_type, tags, and other properties to help the user find what they need\\n\\nFor filters:\\n- Mention available filters to the user if they might be helpful\\n- Use filters ONLY from available_filters in follow-up searches\\n- If a search term matches a filter, do a follow-up search with the filter applied\\n\\nFor pagination:\\n- Show only the first set of results initially\\n- If pagination.hasNextPage is true, ask if the user wants to see more\\n- Only fetch additional pages when explicitly requested\\n\"}"
      }
    ],
    "isError": false
  }
}
```

## 3. UPDATE_CART - Create and update cart

Tool to create a new cart or update an existing cart with items, addresses, and discount codes.

### Example: Create a new cart with a product
```bash
curl -X POST https://gravio-bao-m4.myshopify.com/api/mcp -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "tools/call", "id": 1, "params": {"name": "update_cart", "arguments": {"add_items": [{"product_variant_id": "gid://shopify/ProductVariant/41912405327962", "quantity": 1}]}}}'
```

### Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"instructions\":\"Ask if the customer has found everything they need. If they're ready to check out:\\n\\n1. First help them complete their cart with any additional items they might need\\n2. If the cart contains shipping-eligible items, prompt them to select a shipping option from those available\\n3. Ask if they'd like to add any special instructions or notes to their order (optional)\\n4. Check if they have any discount codes or gift cards they'd like to apply (only if they mention them)\\n5. Assist them in navigating to checkout by providing a markdown link to the checkout URL\\n\\nRemember that buyer information helps calculate accurate shipping rates but isn't required to proceed.\\n\",\"cart\":{\"id\":\"gid://shopify/Cart/Z2NwLWFzaWEtc291dGhlYXN0MTowMUpZMVk4QkVQM0NSQzNZMjVGVFZDMUY0SA?key=2204ddbc1a251a981b4e7015b52a5fae\",\"created_at\":\"2025-06-18T16:34:19.038Z\",\"updated_at\":\"2025-06-18T16:34:19.038Z\",\"lines\":[{\"id\":\"gid://shopify/CartLine/96c635f7-62fe-4739-9d28-6b6c8eca455d?cart=Z2NwLWFzaWEtc291dGhlYXN0MTowMUpZMVk4QkVQM0NSQzNZMjVGVFZDMUY0SA\",\"product_variant_id\":41912405327962,\"quantity\":1,\"attributes\":[],\"cost\":{\"total_amount\":{\"amount\":\"84.0\",\"currency\":\"VND\"},\"subtotal_amount\":{\"amount\":\"84.0\",\"currency\":\"VND\"}},\"applied_discounts\":[]}],\"delivery\":{},\"discounts\":{},\"gift_cards\":[],\"cost\":{\"total_amount\":{\"amount\":\"92.0\",\"currency\":\"VND\"},\"subtotal_amount\":{\"amount\":\"84.0\",\"currency\":\"VND\"},\"total_tax_amount\":{\"amount\":\"8.0\",\"currency\":\"VND\"},\"total_duty_amount\":{}},\"note\":\"\",\"total_quantity\":1,\"checkout_url\":\"https://nitro-apps-bao.myshopify.com/cart/c/Z2NwLWFzaWEtc291dGhlYXN0MTowMUpZMVk4QkVQM0NSQzNZMjVGVFZDMUY0SA?key=2204ddbc1a251a981b4e7015b52a5fae\"},\"errors\":[]}"
      }
    ],
    "isError": false
  }
}
```

## 4. GET_CART - Retrieve cart information

Tool to retrieve detailed cart information by cart ID.

## 5. GET_PRODUCT_DETAILS - Product details

Tool to retrieve detailed product information by ID.

### Example: Get product details
```bash
curl -X POST https://gravio-bao-m4.myshopify.com/api/mcp -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "tools/call", "id": 1, "params": {"name": "get_product_details", "arguments": {"product_id": "gid://shopify/Product/7462477070426"}}}'
```

### Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"product\":{\"product_id\":\"gid://shopify/Product/7462477070426\",\"title\":\"Heart Icon Piqué Polo\",\"description\":\"Product Details FINAL SALE. Cotton piqué polo jersey featuring an embroidered crowned heart motif on the left chest.Two-button placket. Pressed cotton buttons. Flat-knit rib collar and 1x1 ribbed armbands. Split hems. 100% cotton. Knit in the highest quality piqué.Care Instructions: Machine wash cold. Do not tumble dry. Wash inside-out. Size \\u0026 Fit Unisex. This polo fits true-to-size (men's sizing). For specific measurements, refer to the size chart.Zach is 6'0\\\" with a 32\\\" waist and wearing a size M. Provenance "We're known for our fast-paced drops and collaborations, but for a long time, we've wanted to offer more bread-and-butter products — really well-made, versatile staples that speak for themselves and can be part of someone's everyday 'uniform',", explains Rowing Blazers Creative Director and founder Jack Carlson. "Over the past several years, we've resurrected the rugby shirt, made it relevant again, and now we're doing the same thing with our polos."\",\"url\":null,\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"images\":[{\"url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"alt_text\":null},{\"url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241554_396e67d8-f766-4d6e-ae6d-df20360b2083.jpg?v=1746847901\",\"alt_text\":null},{\"url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/77711266-73873_a9eb0792-c224-46f1-9f7c-b4286986c062.jpg?v=1746847901\",\"alt_text\":null},{\"url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/77711266-73882_c9ee5baa-09b9-4c3e-bc0d-844afd569607.jpg?v=1746847901\",\"alt_text\":null},{\"url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/77711266-74026_6d3ddaee-cbe2-44c5-b0dd-2d7dc264ff1a.jpg?v=1746847901\",\"alt_text\":null},{\"url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241557_588c3d95-4dd5-43af-8628-134d87e61887.jpg?v=1746847901\",\"alt_text\":null}],\"options\":[{\"name\":\"Color\",\"values\":[\"White\"]},{\"name\":\"Size\",\"values\":[\"XS\",\"S\",\"M\",\"L\",\"XL\",\"XXL\"]}],\"price_range\":{\"min\":\"84.0\",\"max\":\"84.0\",\"currency\":\"VND\"},\"selectedOrFirstAvailableVariant\":{\"variant_id\":\"gid://shopify/ProductVariant/41912404639834\",\"title\":\"White / XS\",\"inventory\":0,\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0652/4233/3274/files/ROWINGBLAZERS6.4.241548_9dd10baf-5e45-459c-90ab-391196e87e81.jpg?v=1746847901\",\"available\":true}},\"instructions\":\"Use markdown to render product titles as links to their respective product pages using the URL property.\\nPay attention to the selected variant specified in the response.\\n\"}"
      }
    ],
    "isError": false
  }
}
```

## 6. SEARCH_SHOP_POLICIES_AND_FAQS - Search policies and FAQs

Tool to search for store policies, FAQs, and contact information.

### Example: Find return policy
```bash
curl -X POST https://gravio-bao-m4.myshopify.com/api/mcp -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "tools/call", "id": 1, "params": {"name": "search_shop_policies_and_faqs", "arguments": {"query": "return policy", "context": "Customer asking about returns"}}}'
```

### Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "\"Question: Do you accept store credit? Answer: The store accepts store credit as a payment method.\""
      }
    ],
    "isError": false
  }
}
```

## TOOLS SUMMARY

The Shopify MCP system supports 5 main tools:

1. **search_shop_catalog**: Powerful product search with rich filters
2. **update_cart**: Create and manage the cart comprehensively
3. **get_cart**: Retrieve detailed cart information
4. **get_product_details**: Product details and variants
5. **search_shop_policies_and_faqs**: Search store policies and FAQs

## FULL TEST SCRIPT

Bash script to test all tools:

```bash
bash docs/test-all-mcp-tools.sh
```

## QUICK REFERENCE TABLE

| Tool | Purpose | Key parameters |
|------|----------|------------------|
| search_shop_catalog | Product search | query, context, filters, limit |
| update_cart | Cart management | add_items, update_items, discount_codes |
| get_cart | View cart | cart_id |
| get_product_details | Product details | product_id, options |
| search_shop_policies_and_faqs | Search policies/FAQ | query, context |

---

**Document generated by:** AI Assistant
**Created date:** 18/06/2025 23:40
**Endpoint test:** https://gravio-bao-m4.myshopify.com/api/mcp

---

## Live test results (gravio-bao-m4)

The following are fresh outputs captured from running `bash docs/test-all-mcp-tools.sh` against `https://gravio-bao-m4.myshopify.com/api/mcp`.

### search_shop_catalog (query: "polo shirt", limit: 2)
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"products\":[{\"product_id\":\"gid://shopify/Product/7777256145014\",\"title\":\"Fun Shirt\",\"description\":\"Product Details A loving homage to the original, authentic “Fun Shirt” featuring an embroidered crowned heart motif on the lower left torso.Soft S-roll button-down collar. Pure cotton buttons. American placket. 100% cotton.Care Instructions: Dry clean only. Size \\\u0026 Fit Unisex (men’s sizing). This Oxford has a slim, tailored fit through the body; for a roomier fit, we recommend sizing up. For specific measurements, refer to the size chart.Cami is 5'11\\\" with a 26\\\" waist and wearing a size M.\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0645/6167/6406/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT.jpg?v=1752141589\",\"price_range\":{\"min\":\"118.0\",\"max\":\"118.0\",\"currency\":\"VND\"},\"product_type\":\"Polos \\\u0026 Dress Shirts\",\"tags\":[\"All Tops\",\"Dress Shirts\",\"Final Sale\",\"Heart Icon\",\"July24\",\"New\",\"RB Brand\",\"Shop All\",\"summer24\"],\"variants\":[{\"variant_id\":\"gid://shopify/ProductVariant/42376773501046\",\"title\":\"Fun Shirt Multi-Stripe / XS\",\"price\":\"118.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0645/6167/6406/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT.jpg?v=1752141589\",\"available\":true}]},{\"product_id\":\"gid://shopify/Product/7777259585654\",\"title\":\"Heart Icon Piqué Polo\",\"description\":\"Product Details FINAL SALE. Cotton piqué polo jersey featuring an embroidered crowned heart motif on the left chest.Two-button placket. Pressed cotton buttons. Flat-knit rib collar and 1x1 ribbed armbands. Split hems. 100% cotton. Knit in the highest quality piqué.Care Instructions: Machine wash cold. Do not tumble dry. Wash inside-out. Size \\\u0026 Fit Unisex. This polo fits true-to-size (men’s sizing). For specific measurements, refer to the size chart. Provenance “We’re known for our fast-paced drops and collaborations, but for a long time, we’ve wanted to offer more bread-and-butter products — really well-made, versatile staples that speak for themselves and can be part of someone’s everyday ‘uniform’,” explains Rowing Blazers Creative Director and founder Jack Carlson. “Over the past several years, we’ve resurrected the rugby shirt, made it relevant again, and now we’re doing the same thing with our polos.”\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0645/6167/6406/files/ROWINGBLAZERS6.4.241538.jpg?v=1752141877\",\"price_range\":{\"min\":\"84.0\",\"max\":\"84.0\",\"currency\":\"VND\"},\"product_type\":\"Polos \\\u0026 Dress Shirts\",\"tags\":[\"All Tops\",\"final-sale\",\"Heart Icon\",\"July24\",\"New\",\"Polos\",\"RB Brand\",\"Shop All\",\"summer24\"],\"variants\":[{\"variant_id\":\"gid://shopify/ProductVariant/42376793653366\",\"title\":\"Light Blue / XS\",\"price\":\"84.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0645/6167/6406/files/ROWINGBLAZERS6.4.241538.jpg?v=1752141877\",\"available\":true}]}],\"pagination\":{\"hasNextPage\":true,\"hasPreviousPage\":false,\"startCursor\":\"eyJwYWdlIjoxLCJsYXN0X2lkIjo3Nzc3MjU2MTQ1MDE0LCJyZXZlcnNlIjp0cnVlLCJvZmZzZXQiOjB9\",\"endCursor\":\"eyJwYWdlIjoyLCJsYXN0X2lkIjo3Nzc3MjU5NTg1NjU0LCJyZXZlcnNlIjp0cnVlLCJvZmZzZXQiOjF9\",\"currentPage\":1,\"nextPage\":2,\"maxPages\":12500,\"limitReached\":false},\"available_filters\":[{\"label\":\"Availability\",\"values\":{\"label\":[\"In stock\",\"Out of stock\"],\"input_options\":[{\"label\":\"In stock\",\"input\":{\"available\":true}},{\"label\":\"Out of stock\",\"input\":{\"available\":false}}]}},{\"label\":\"Price\",\"values\":{\"label\":[\"Price\"],\"input_options\":[{\"label\":\"Price\",\"input\":{\"price\":{\"min\":0,\"max\":268.0}}}]}}],\"instructions\":\"Use markdown to render product titles as links to their respective product pages using the URL property.\\n\\nFor product data:\\n- If variants are included in the response, those are the only variants available\\n- If variants are not included, use the options and availability matrix with get_product_details tool\\n- Check product_type, tags, and other properties to help the user find what they need\\n\\nFor filters:\\n- Mention available filters to the user if they might be helpful\\n- Use filters ONLY from available_filters in follow-up searches\\n- If a search term matches a filter, do a follow-up search with the filter applied\\n\\nFor pagination:\\n- Show only the first set of results initially\\n- If pagination.hasNextPage is true, ask if the user wants to see more\\n- Only fetch additional pages when explicitly requested\\n\"}"
      }
    ],
    "isError": false
  }
}
```

### update_cart (using first variant from search)
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"instructions\":\"Ask if the customer has found everything they need. If they're ready to check out:\\n\\n1. First help them complete their cart with any additional items they might need\\n2. If the cart contains shipping-eligible items, prompt them to select a shipping option from those available\\n3. Ask if they'd like to add any special instructions or notes to their order (optional)\\n4. Check if they have any discount codes or gift cards they'd like to apply (only if they mention them)\\n5. Assist them in navigating to checkout by providing a markdown link to the checkout URL\\n\\nRemember that buyer information helps calculate accurate shipping rates but isn't required to proceed.\\n\",\"cart\":{\"id\":\"gid://shopify/Cart/hWN1m8SAXQWpRlTxaPvQEMUO?key=367c1b875bd038302a146c22808a0df2\",\"created_at\":\"2025-08-14T03:15:42.517Z\",\"updated_at\":\"2025-08-14T03:15:42.517Z\",\"lines\":[{\"id\":\"gid://shopify/CartLine/d700e634-084d-472a-881a-cfaee01d7e4f?cart=hWN1m8SAXQWpRlTxaPvQEMUO\",\"quantity\":1,\"cost\":{\"total_amount\":{\"amount\":\"118.0\",\"currency\":\"VND\"},\"subtotal_amount\":{\"amount\":\"118.0\",\"currency\":\"VND\"}},\"merchandise\":{\"id\":\"gid://shopify/ProductVariant/42376773501046\",\"title\":\"Fun Shirt Multi-Stripe / XS\",\"product\":{\"id\":\"gid://shopify/Product/7777256145014\",\"title\":\"Fun Shirt\"}}}],\"delivery\":{},\"discounts\":{},\"gift_cards\":[],\"cost\":{\"total_amount\":{\"amount\":\"130.0\",\"currency\":\"VND\"},\"subtotal_amount\":{\"amount\":\"118.0\",\"currency\":\"VND\"},\"total_tax_amount\":{\"amount\":\"12.0\",\"currency\":\"VND\"}},\"total_quantity\":1,\"checkout_url\":\"https://gravio-bao-m4.myshopify.com/cart/c/hWN1m8SAXQWpRlTxaPvQEMUO?key=367c1b875bd038302a146c22808a0df2\"},\"errors\":[]}"
      }
    ],
    "isError": false
  }
}
```

### get_cart (using created cart id)
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"instructions\":\"Ask if the customer has found everything they need. If they're ready to check out:\\n\\n1. First help them complete their cart with any additional items they might need\\n2. If the cart contains shipping-eligible items, prompt them to select a shipping option from those available\\n3. Ask if they'd like to add any special instructions or notes to their order (optional)\\n4. Check if they have any discount codes or gift cards they'd like to apply (only if they mention them)\\n5. Assist them in navigating to checkout by providing a markdown link to the checkout URL\\n\\nRemember that buyer information helps calculate accurate shipping rates but isn't required to proceed.\\n\",\"cart\":{\"id\":\"gid://shopify/Cart/hWN1m8SAXQWpRlTxaPvQEMUO?key=367c1b875bd038302a146c22808a0df2\",\"created_at\":\"2025-08-14T03:15:42.517Z\",\"updated_at\":\"2025-08-14T03:15:42.517Z\",\"lines\":[{\"id\":\"gid://shopify/CartLine/d700e634-084d-472a-881a-cfaee01d7e4f?cart=hWN1m8SAXQWpRlTxaPvQEMUO\",\"quantity\":1,\"cost\":{\"total_amount\":{\"amount\":\"118.0\",\"currency\":\"VND\"},\"subtotal_amount\":{\"amount\":\"118.0\",\"currency\":\"VND\"}},\"merchandise\":{\"id\":\"gid://shopify/ProductVariant/42376773501046\",\"title\":\"Fun Shirt Multi-Stripe / XS\",\"product\":{\"id\":\"gid://shopify/Product/7777256145014\",\"title\":\"Fun Shirt\"}}}],\"delivery\":{},\"discounts\":{},\"gift_cards\":[],\"cost\":{\"total_amount\":{\"amount\":\"130.0\",\"currency\":\"VND\"},\"subtotal_amount\":{\"amount\":\"118.0\",\"currency\":\"VND\"},\"total_tax_amount\":{\"amount\":\"12.0\",\"currency\":\"VND\"}},\"total_quantity\":1,\"checkout_url\":\"https://gravio-bao-m4.myshopify.com/cart/c/hWN1m8SAXQWpRlTxaPvQEMUO?key=367c1b875bd038302a146c22808a0df2\"},\"errors\":[]}"
      }
    ],
    "isError": false
  }
}
```

### get_product_details (using first product from search)
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"product\":{\"product_id\":\"gid://shopify/Product/7777256145014\",\"title\":\"Fun Shirt\",\"description\":\"Product Details A loving homage to the original, authentic “Fun Shirt” featuring an embroidered crowned heart motif on the lower left torso.Soft S-roll button-down collar. Pure cotton buttons. American placket. 100% cotton.Care Instructions: Dry clean only. Size \\\u0026 Fit Unisex (men’s sizing). This Oxford has a slim, tailored fit through the body; for a roomier fit, we recommend sizing up. For specific measurements, refer to the size chart.Cami is 5'11\\\" with a 26\\\" waist and wearing a size M.\",\"url\":null,\"image_url\":\"https://cdn.shopify.com/s/files/1/0645/6167/6406/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT.jpg?v=1752141589\",\"images\":[{\"url\":\"https://cdn.shopify.com/s/files/1/0645/6167/6406/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT.jpg?v=1752141589\",\"alt_text\":null}],\"options\":[{\"name\":\"Color\",\"values\":[\"Fun Shirt Multi-Stripe\"]},{\"name\":\"Size\",\"values\":[\"XS\",\"S\",\"M\",\"L\",\"XL\",\"XXL\"]}],\"price_range\":{\"min\":\"118.0\",\"max\":\"118.0\",\"currency\":\"VND\"},\"selectedOrFirstAvailableVariant\":{\"variant_id\":\"gid://shopify/ProductVariant/42376773501046\",\"title\":\"Fun Shirt Multi-Stripe / XS\",\"price\":\"118.0\",\"currency\":\"VND\",\"image_url\":\"https://cdn.shopify.com/s/files/1/0645/6167/6406/files/RB-06JUNE24-SHIRTMULTICOLOR-FRONT.jpg?v=1752141589\",\"available\":true}},\"instructions\":\"Use markdown to render product titles as links to their respective product pages using the URL property.\\nPay attention to the selected variant specified in the response.\\n\"}"
      }
    ],
    "isError": false
  }
}
```

### search_shop_policies_and_faqs (query: "return policy")
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"question\":\"Do you accept store credit?\",\"answer\":\"The store accepts store credit as a payment method.\"}]"
      }
    ],
    "isError": false
  }
}
```
