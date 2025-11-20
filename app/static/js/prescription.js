function printLabel() {
    const dataEl = document.getElementById('prescription-data');
    const chi_tiet = JSON.parse(dataEl.textContent);
    const MaDT = chi_tiet.length > 0 ? chi_tiet[0].MaDT || '' : '';

    const printWindow = window.open('', '', 'height=500,width=800');
    printWindow.document.write('<html><head><title>Nhãn Thuốc</title></head><body>');
    printWindow.document.write('<h3>Nhãn Thuốc Cho Đơn #' + MaDT + '</h3>');
    printWindow.document.write('<table border="1"><thead><tr><th>Thuốc</th><th>Liều</th><th>Ghi Chú</th></tr></thead><tbody>');

    for (let i = 0; i < chi_tiet.length; i++) {
        const ct = chi_tiet[i];
        printWindow.document.write('<tr><td>' + ct.thuoc.TenThuoc + '</td><td>' + ct.LieuDung + '</td><td>' + ct.GhiChu + '</td></tr>');
    }

    printWindow.document.write('</tbody></table></body></html>');
    printWindow.document.close();
    printWindow.print();
}
