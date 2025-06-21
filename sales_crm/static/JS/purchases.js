// AJAX لبيانات المنتج
$(document).ready(function() {
    $('.product-select').on('change', function() {
        const productId = $(this).val();
        if (productId) {
            $.ajax({
                url: '/purchases/get-product-data/',
                data: { 'product_id': productId },
                dataType: 'json',
                success: function(data) {
                    const row = $(this).closest('tr');
                    row.find('.unit-cost').val(data.cost);
                    row.find('.quantity').val(1);
                    row.find('.total-cost').text(data.cost);
                    calculateGrandTotal();
                }.bind(this)
            });
        }
    });
});