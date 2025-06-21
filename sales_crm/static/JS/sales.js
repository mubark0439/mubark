document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('sale-items-container');
    const addButton = document.getElementById('add-item');
    const template = document.getElementById('item-template');
    const discountInput = document.getElementById('id_discount');
    
    // Add new item
    addButton.addEventListener('click', function() {
        const newItem = template.cloneNode(true);
        newItem.style.display = 'block';
        newItem.classList.remove('sale-item');
        newItem.id = '';
        container.appendChild(newItem);
        
        // Add event listeners to new item
        setupItemEvents(newItem);
    });
    
    // Setup events for an item
    function setupItemEvents(item) {
        const productSelect = item.querySelector('.product-select');
        const quantityInput = item.querySelector('.quantity-input');
        const priceInput = item.querySelector('.price-input');
        const totalInput = item.querySelector('.total-input');
        const removeBtn = item.querySelector('.remove-item');
        
        // Update price when product changes
        productSelect.addEventListener('change', function() {
            const price = this.options[this.selectedIndex]?.dataset.price || 0;
            priceInput.value = parseFloat(price).toFixed(2);
            updateItemTotal();
        });
        
        // Update total when quantity changes
        quantityInput.addEventListener('input', updateItemTotal);
        
        // Remove item
        removeBtn.addEventListener('click', function() {
            item.remove();
            updateInvoiceTotal();
        });
        
        function updateItemTotal() {
            const price = parseFloat(priceInput.value) || 0;
            const quantity = parseInt(quantityInput.value) || 0;
            const total = price * quantity;
            totalInput.value = total.toFixed(2);
            updateInvoiceTotal();
        }
    }
    
    // Update invoice totals
    function updateInvoiceTotal() {
        let subtotal = 0;
        const items = container.querySelectorAll('[id^="item-template"]');
        
        items.forEach(item => {
            const total = parseFloat(item.querySelector('.total-input').value) || 0;
            subtotal += total;
        });
        
        const discount = parseFloat(discountInput.value) || 0;
        const total = subtotal - discount;
        
        document.getElementById('subtotal').textContent = subtotal.toFixed(2) + ' ر.س';
        document.getElementById('discount-amount').textContent = discount.toFixed(2) + ' ر.س';
        document.getElementById('total-amount').textContent = total.toFixed(2) + ' ر.س';
    }
    
    // Update totals when discount changes
    discountInput.addEventListener('input', updateInvoiceTotal);
    
    // Add first item by default
    addButton.click();
});