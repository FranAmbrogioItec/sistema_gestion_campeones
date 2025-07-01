/*!
* Start Bootstrap - Simple Sidebar v6.0.6 (https://startbootstrap.com/template/simple-sidebar)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/simple-sidebar/blob/master/LICENSE)
*/
//
// Scripts
//

window.addEventListener('DOMContentLoaded', event => {
    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment the following line to restore sidebar toggle on desktop
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            // localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }
});

let movimientoIdEliminar = null;

function editarMovimiento(id, tipo, monto, motivo) {
    document.getElementById('formEditarMovimiento').action = `/modificar_movimiento/${id}`;
    document.getElementById('editTipo').value = tipo;
    document.getElementById('editMonto').value = monto;
    document.getElementById('editMotivo').value = motivo;
}

function confirmarEliminar(id) {
    movimientoIdEliminar = id;
    document.getElementById('formEliminar').action = `/eliminar_movimiento/${id}`;
}