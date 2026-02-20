---
description: Advanced Billing Workflow (GST & Discounts)
---

# Professional Billing Workflow

Follow these steps to generate accurate invoices with item-wise GST and professional discounts.

## 1. Configure Tax Rates

Before billing, ensure your tax rates are correctly set up to automate the calculation.

### A. Global Default Tax

- Go to **Settings** > **Billing Settings**.
- Set the **Default GST Rate** (e.g., 18%). This applies to any item without a specific category or product tax rate.

### B. Category-Specific GST

- Navigate to **Manage** > **Categories**.
- Edit a category (e.g., "Beverages") and set a **GST Percentage** (e.g., 5%).
- All products in this category will now automatically use the 5% rate unless overridden.

### C. Product-Specific GST (Override)

- Navigate to **Manage** > **Products**.
- Edit a specific product (e.g., "Premium Coffee").
- Set the **Product GST %** if you need to override the category's default rate.

## 2. New Bill Creation

// turbo

1. Navigate to the **New Bill** section (billing.html).
2. **Select Products**: Click on product cards to add them to the cart.
   - **Note**: Tax and discounts are NOT shown or calculated at this stage. You will only see the base subtotal.
3. **Select/Add Customer**: (Optional) Search for an existing customer.

## 3. Checkout & Professional Calculation

1. Click the **Checkout** button to begin the payment process.
2. **Review Breakdown**: In the checkout modal, the system now calculates:
   - **GST (Tax)**: Based on item-wise rates.
   - **Subtotal Items**: Sum of base prices.
3. **Apply Discount**: Enter the discount percentage (e.g., 10%) in the modal.
   - The system instantly updates the **Final Total**.
4. **Complete Payment**: Select payment method and status.

## 4. Invoice Printing

1. Once payment is completed, the system generates the final invoice.
2. The **printed invoice** will now clearly display:
   - Itemized tax details.
   - Total GST.
   - Applied discount percentage/amount.
   - Final Grand Total.

## 5. Review and Print

1. View the generated invoice in the **Invoices** section.
2. Verify the professional layout:
   - **Subtotal**: Base price of items.
   - **GST**: Sum of item-wise taxes.
   - **Discount**: Clearly displayed discount amount.
   - **Grand Total**: Final settlement amount.
3. Click **Print** to generate the thermal receipt or PDF invoice for the customer.
