function exportTableToExcel(tableId, fileName) {
    // Obtén la tabla por ID
    const table = document.getElementById(tableId);
    const workbook = XLSX.utils.table_to_book(table, { sheet: "Sheet1" });
    // Exporta a un archivo Excel
    XLSX.writeFile(workbook, fileName);
}
