$(document).ready(function () {
    // Khởi tạo Select2 cho thuốc
    $('.medicine-select').select2({
        width: '100%'
    });

    // Khởi tạo date picker cho ngày tái khám
    flatpickr("#canhbao_taikham", {
        locale: "vn",
        dateFormat: "Y-m-d",
        minDate: "today"
    });

    // Thêm thuốc mới
    $('#add-prescription').click(function () {
        const newItem = $('.prescription-item:first').clone();

        // Xóa giá trị cũ
        newItem.find('select').val('').trigger('change');
        newItem.find('input').val('');

        $('#prescription-container').append(newItem);

        // Khởi tạo lại Select2
        newItem.find('.medicine-select').select2({
            width: '100%'
        });
    });

    // Xóa thuốc
    $(document).on('click', '.remove-prescription', function () {
        if ($('.prescription-item').length > 1) {
            $(this).closest('.prescription-item').remove();
        } else {
            alert('Phải có ít nhất một thuốc trong đơn!');
        }
    });

    // Kiểm tra tương tác thuốc khi thay đổi thuốc
    $(document).on('change', '.medicine-select', function () {
        checkDrugInteractions();
        checkAllergyWarnings();
    });

    function checkDrugInteractions() {
        const drugIds = [];
        $('.medicine-select').each(function () {
            const value = $(this).val();
            if (value) {
                drugIds.push(parseInt(value));
            }
        });

        if (drugIds.length < 2) {
            $('#interaction-alerts').empty();
            return;
        }

        $.ajax({
            url: checkInteractionsUrl,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ drug_ids: drugIds }),
            success: function (response) {
                displayInteractions(response.interactions);
            }
        });
    }

    function checkAllergyWarnings() {
        const drugIds = [];
        $('.medicine-select').each(function () {
            const value = $(this).val();
            if (value) {
                drugIds.push(parseInt(value));
            }
        });

        if (drugIds.length < 1) {
            $('#allergy-alerts').empty();
            return;
        }

        $.ajax({
            url: checkAllergyUrl,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                drug_ids: drugIds,
                patient_id: patientId
            }),
            success: function (response) {
                displayAllergyWarnings(response.warnings);
            }
        });
    }

    function displayInteractions(interactions) {
        const container = $('#interaction-alerts');
        container.empty();

        if (interactions.length === 0) return;

        const alertClass = interactions.some(i => i.severity === 'Nghiêm trọng') ? 'alert-danger' :
            interactions.some(i => i.severity === 'Trung bình') ? 'alert-warning' : 'alert-info';

        const alertHtml = `
            <div class="alert ${alertClass}">
                <h6>Cảnh báo tương tác thuốc:</h6>
                <ul>
                    ${interactions.map(i => `<li><strong>${i.drug1} + ${i.drug2}:</strong> ${i.description} (${i.severity})</li>`).join('')}
                </ul>
            </div>
        `;

        container.html(alertHtml);
    }

    function displayAllergyWarnings(warnings) {
        const container = $('#allergy-alerts');
        container.empty();

        if (warnings.length === 0) return;

        const alertHtml = `
            <div class="alert alert-danger">
                <h6>Cảnh báo dị ứng:</h6>
                <ul>
                    ${warnings.map(w => `<li><strong>${w.drug}:</strong> Dị ứng với ${w.allergen} - ${w.reaction}</li>`).join('')}
                </ul>
            </div>
        `;

        container.html(alertHtml);
    }

    // Kiểm tra tương tác thuốc và dị ứng khi tải trang
    checkDrugInteractions();
    checkAllergyWarnings();
});
