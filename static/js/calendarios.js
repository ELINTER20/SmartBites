document.addEventListener('DOMContentLoaded', function () {
  const nutriologos = window.nutriologosData;

  if (!nutriologos || !Array.isArray(nutriologos)) {
    console.error("Datos de nutriólogos no disponibles.");
    return;
  }

  nutriologos.forEach(nutri => {
    const calendarEl = document.getElementById(`calendar${nutri.id_nutriologo}`);
    if (calendarEl) {
      const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        height: 500,
        selectable: true,
        headerToolbar: {
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek'
        },
        dateClick: function(info) {
          alert(`Has seleccionado: ${info.dateStr} con ${nutri.nombre_completo}`);
        }
      });
      calendar.render();
    }
  });
});