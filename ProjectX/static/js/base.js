const filenameMap = {
  deptTable: "DepartmentList",
  branchTable: "BranchList",
  userTable: "UserList",
  countryTable: "CountryList",
  designationTable: "DesignationList",
  patientTable: "PatientList",
  hospitalTable: "HospitalList",
  appointmentTable: "AppointmentList",
  districtTable: "DistrictList",
  stateTable: "StateList"
};

function exportToExcel(tableId) {
  const table = document.getElementById(tableId);
  if (!table) return alert("Table not found.");

  const wb = XLSX.utils.table_to_book(table, { sheet: "Sheet1" });
  const name = filenameMap[tableId] || "Export";
  XLSX.writeFile(wb, `${name}.xlsx`);
}

async function exportToPDF(tableId) {
  const table = document.getElementById(tableId);
  if (!table) return alert("Table not found.");

  const tableClone = table.cloneNode(true);

  if (tableId === "deptTable") {
    tableClone.querySelectorAll("thead tr").forEach(row => {
      if (row.cells.length > 1) row.deleteCell(-1);
    });
    tableClone.querySelectorAll("tbody tr").forEach(row => {
      if (row.cells.length > 1) row.deleteCell(-1);
    });
  }
  tableClone.style.width = "100%";
  tableClone.style.borderCollapse = "collapse";
  tableClone.style.fontSize = "12px";

  const container = document.createElement("div");
  container.style.position = "fixed";
  container.style.top = "-10000px";
  container.style.width = "1000px"; // force full width
  container.appendChild(tableClone);
  document.body.appendChild(container);

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF("landscape", "pt", "a4");
  const name = filenameMap[tableId] || "ExportedReport";

  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text(name.replace("List", " List"), 40, 40);

  const canvas = await html2canvas(tableClone, {
    scale: 2, // Higher scale = better quality
    useCORS: true
  });

  const imgData = canvas.toDataURL("image/png");
  const imgProps = doc.getImageProperties(imgData);
  const pdfWidth = doc.internal.pageSize.getWidth() - 80;
  const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

  doc.addImage(imgData, "PNG", 40, 60, pdfWidth, pdfHeight);
  doc.save(`${name}.pdf`);

  document.body.removeChild(container);
}

function toggleMinimize() {
  document.getElementById("contentBox")?.classList.toggle("minimized");
}


function closeContent() {
  document.getElementById("contentBox")?.remove();
}

document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(() => {
      alert.classList.remove('show');
      alert.classList.add('fade');
      setTimeout(() => alert.remove(), 8000); // remove from DOM after fade out
    }, 7000); // 4 seconds
  });
});


function exportTableWithoutActions(tableId, titleText) {
  const originalTable = document.getElementById(tableId);
  if (!originalTable) return alert("Table not found");

  const clonedTable = originalTable.cloneNode(true);
  for (let row of clonedTable.querySelectorAll('tr')) {
    if (row.cells.length > 1) {
      row.deleteCell(row.cells.length - 1);
    }
  }

  const container = document.createElement('div');
  const title = document.createElement('h2');
  title.textContent = titleText;
  title.style.textAlign = 'center';
  title.style.fontFamily = 'Arial, sans-serif';
  title.style.marginBottom = '20px';
  container.appendChild(title);
  container.appendChild(clonedTable);

  clonedTable.style.width = '100%';
  clonedTable.style.borderCollapse = 'collapse';
  clonedTable.style.fontSize = '12px';

  for (let row of clonedTable.rows) {
    for (let cell of row.cells) {
      cell.style.border = '1px solid #999';
      cell.style.padding = '5px';
      cell.style.fontFamily = 'Arial, sans-serif';
    }
  }

  html2pdf().set({
    margin: 0.5,
    filename: titleText.replace(/\s+/g, '') + '.pdf',
    html2canvas: { scale: 2 },
    jsPDF: { orientation: 'portrait', unit: 'in', format: 'letter' }
  }).from(container).save();
}

