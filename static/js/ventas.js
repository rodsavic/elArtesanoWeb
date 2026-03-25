function inicializarSelects() {
    $('.selectProducto').select2({
        placeholder: "Selecciona un producto",
        allowClear: true
    });
    $('#cliente').select2({
        placeholder: "Selecciona un cliente",
        allowClear: true
    });
}

function syncTipoVentaHiddenInput() {
    const hiddenTipoVenta = document.getElementById("tipo_venta");
    const checked = document.querySelector('.tipo-venta-check:checked');
    if (hiddenTipoVenta) {
        hiddenTipoVenta.value = checked ? checked.value : "";
    }
}

function obtenerPrecioLista(opcionProducto) {
    return parseFloat(opcionProducto?.getAttribute('data-precio')) || 0;
}

function calcularIva(totalDetalle, ivaDescripcion) {
    let iva10 = 0;
    let iva5 = 0;
    if (ivaDescripcion === 10) {
        iva10 = totalDetalle / 11;
    } else if (ivaDescripcion === 5) {
        iva5 = totalDetalle / 21;
    }
    return { iva10, iva5 };
}

function serializarFila(fila) {
    const idProducto = fila.getAttribute('data-producto-id');
    const cantidad = parseInt(fila.querySelector('.cantidad-producto-input')?.value, 10) || 1;
    const precioLista = parseFloat(fila.querySelector('.precio-lista-cell')?.innerText) || 0;
    const precioUnitario = parseFloat(fila.querySelector('.precio-unitario-input')?.value) || 0;
    const totalDetalle = parseFloat(fila.querySelector('.total-detalle-cell')?.innerText) || 0;
    const iva10 = parseFloat(fila.querySelector('.iva10-cell')?.innerText) || 0;
    const iva5 = parseFloat(fila.querySelector('.iva5-cell')?.innerText) || 0;

    return {
        id_producto: idProducto,
        cantidad,
        precio_lista: precioLista.toFixed(0),
        precio_unitario: precioUnitario.toFixed(0),
        total_detalle: totalDetalle.toFixed(0),
        total_detalle_iva_10: iva10.toFixed(0),
        total_detalle_iva_5: iva5.toFixed(0),
    };
}

function serializarTablaProductos() {
    const tabla = document.getElementById("tablaProductos")?.querySelector("tbody");
    if (!tabla) return [];
    return Array.from(tabla.rows).map(serializarFila);
}

function recalcularFila(fila) {
    const cantidadInput = fila.querySelector('.cantidad-producto-input');
    const precioUnitarioInput = fila.querySelector('.precio-unitario-input');
    const ivaDescripcion = parseInt(fila.getAttribute('data-iva'), 10) || 0;

    let cantidad = parseInt(cantidadInput?.value, 10);
    if (Number.isNaN(cantidad) || cantidad < 1) cantidad = 1;
    cantidadInput.value = String(cantidad);

    let precioUnitario = parseFloat(precioUnitarioInput?.value);
    if (Number.isNaN(precioUnitario) || precioUnitario < 0) precioUnitario = 0;
    precioUnitarioInput.value = precioUnitario.toFixed(0);

    const totalDetalle = cantidad * precioUnitario;
    const { iva10, iva5 } = calcularIva(totalDetalle, ivaDescripcion);

    fila.querySelector('.total-detalle-cell').innerText = totalDetalle.toFixed(0);
    fila.querySelector('.iva10-cell').innerText = iva10.toFixed(0);
    fila.querySelector('.iva5-cell').innerText = iva5.toFixed(0);
}

function recalcularTotalesDesdeTabla() {
    const tabla = document.getElementById("tablaProductos")?.querySelector("tbody");
    const totalVentaInput = document.getElementById("total_venta");
    const totalIva10Input = document.getElementById("total_iva_10");
    const totalIva5Input = document.getElementById("total_iva_5");
    if (!tabla || !totalVentaInput || !totalIva10Input || !totalIva5Input) return;

    let totalVenta = 0;
    let totalIva10 = 0;
    let totalIva5 = 0;

    Array.from(tabla.rows).forEach((fila) => {
        recalcularFila(fila);
        totalVenta += parseFloat(fila.querySelector('.total-detalle-cell')?.innerText) || 0;
        totalIva10 += parseFloat(fila.querySelector('.iva10-cell')?.innerText) || 0;
        totalIva5 += parseFloat(fila.querySelector('.iva5-cell')?.innerText) || 0;
    });

    totalVentaInput.value = totalVenta.toFixed(0);
    totalIva10Input.value = totalIva10.toFixed(0);
    totalIva5Input.value = totalIva5.toFixed(0);

    const totalVentaModal = document.getElementById("totalVentaModal");
    if (totalVentaModal) {
        totalVentaModal.value = totalVenta.toFixed(0);
    }

    const productosJsonInput = document.getElementById('productos_json');
    if (productosJsonInput) {
        productosJsonInput.value = JSON.stringify(serializarTablaProductos());
    }
}

function agregarProductoATabla() {
    syncTipoVentaHiddenInput();
    const selectProducto = document.getElementById("selectProducto");
    const cantidadInput = document.getElementById("cantidad");
    const opcionSeleccionada = selectProducto.options[selectProducto.selectedIndex];

    if (!opcionSeleccionada || !selectProducto.value) {
        alert("Selecciona un producto valido.");
        return;
    }

    const cantidad = parseInt(cantidadInput.value, 10) || 0;
    if (cantidad <= 0) {
        alert("Selecciona una cantidad valida.");
        return;
    }

    const idProducto = selectProducto.value;
    const tabla = document.getElementById("tablaProductos").querySelector("tbody");
    let filaExistente = tabla.querySelector(`tr[data-producto-id='${idProducto}']`);

    if (filaExistente) {
        const cantidadActual = parseInt(filaExistente.querySelector('.cantidad-producto-input')?.value, 10) || 1;
        filaExistente.querySelector('.cantidad-producto-input').value = cantidadActual + cantidad;
        recalcularTotalesDesdeTabla();
        cantidadInput.value = 1;
        return;
    }

    const precioLista = obtenerPrecioLista(opcionSeleccionada);
    const ivaDescripcion = parseInt(opcionSeleccionada.getAttribute('data-descripcionIva'), 10) || 0;
    const nombreProducto = opcionSeleccionada.text;

    const nuevaFila = tabla.insertRow();
    nuevaFila.setAttribute('data-producto-id', idProducto);
    nuevaFila.setAttribute('data-iva', ivaDescripcion);

    nuevaFila.innerHTML = `
        <td>${nombreProducto}</td>
        <td><input type="number" min="1" step="1" class="form-control form-control-sm text-center cantidad-producto-input" value="${cantidad}"></td>
        <td class="precio-lista-cell">${precioLista.toFixed(0)}</td>
        <td><input type="number" min="0" step="1" class="form-control form-control-sm text-center precio-unitario-input" value="${precioLista.toFixed(0)}"></td>
        <td class="total-detalle-cell">0</td>
        <td class="iva10-cell">0</td>
        <td class="iva5-cell">0</td>
        <td><button type="button" class="btn-cancelar btn-sm" title="Eliminar" onclick="eliminarProducto('${idProducto}')"><i class="bi bi-trash"></i></button></td>
    `;

    recalcularTotalesDesdeTabla();
    cantidadInput.value = 1;
}

function eliminarProducto(idProducto) {
    const fila = document.querySelector(`tr[data-producto-id='${idProducto}']`);
    if (fila) {
        fila.remove();
        recalcularTotalesDesdeTabla();
    }
}

function abrirModalVuelto() {
    if (document.getElementById("cliente").value === "") {
        alert("Por favor, selecciona un cliente antes de continuar.");
        return;
    }

    const totalVenta = parseFloat(document.getElementById("total_venta").value) || 0;
    if (totalVenta === 0) {
        alert("No hay productos en la venta.");
        return;
    }

    document.getElementById("totalVentaModal").value = totalVenta.toFixed(0);
    ['efectivo', 'pos', 'transferencia'].forEach((id) => {
        const input = document.getElementById(id);
        if (!input) return;
        const defaultValue = input.getAttribute('data-default');
        input.value = defaultValue !== null ? defaultValue : "";
    });
    document.getElementById("mensajeVuelto").textContent = "";

    const modalElement = document.getElementById('modalCobro');
    modalElement.style.display = 'block';
    modalElement.classList.add('show');
    modalElement.setAttribute('aria-modal', 'true');
    modalElement.setAttribute('aria-hidden', 'false');

    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop fade show';
    backdrop.id = 'modal-backdrop';
    document.body.appendChild(backdrop);
    document.body.classList.add('modal-open');
}

function cerrarModal() {
    const modalElement = document.getElementById('modalCobro');
    const backdrop = document.getElementById('modal-backdrop');

    modalElement.style.display = 'none';
    modalElement.classList.remove('show');
    modalElement.setAttribute('aria-hidden', 'true');
    modalElement.removeAttribute('aria-modal');
    if (backdrop) backdrop.remove();
    document.body.classList.remove('modal-open');
}

function calcularVuelto() {
    const totalVenta = parseFloat(document.getElementById("total_venta").value) || 0;
    const montoEfectivo = parseFloat(document.getElementById("efectivo").value) || 0;
    const montoPos = parseFloat(document.getElementById("pos").value) || 0;
    const montoTransferencia = parseFloat(document.getElementById("transferencia").value) || 0;
    const mensajeVuelto = document.getElementById("mensajeVuelto");
    const montoApagar = totalVenta - montoPos - montoTransferencia;

    if (montoEfectivo >= montoApagar) {
        const vuelto = montoEfectivo - montoApagar;
        mensajeVuelto.textContent = `Vuelto: Gs ${vuelto.toFixed(0)}`;
    } else {
        mensajeVuelto.textContent = "Monto recibido insuficiente para cubrir la venta.";
    }
}

function enviarFormulario() {
    const totalVenta = parseFloat(document.getElementById("total_venta").value) || 0;
    const montoEfectivo = parseFloat(document.getElementById("efectivo").value) || 0;
    const montoPos = parseFloat(document.getElementById("pos").value) || 0;
    const montoTransferencia = parseFloat(document.getElementById("transferencia").value) || 0;
    const montoPagado = montoEfectivo + montoPos + montoTransferencia;

    if (montoPagado < totalVenta) {
        window.alert('No se ha pagado el total de la venta');
        return;
    }

    document.getElementById('productos_json').value = JSON.stringify(serializarTablaProductos());
    document.querySelector("form").submit();
}

document.addEventListener('DOMContentLoaded', function() {
    const tipoVentaChecks = Array.from(document.querySelectorAll('.tipo-venta-check'));
    if (tipoVentaChecks.length > 0) {
        if (!tipoVentaChecks.some(chk => chk.checked)) {
            tipoVentaChecks[0].checked = true;
        }
        tipoVentaChecks.forEach((check) => {
            check.addEventListener('change', function () {
                if (this.checked) {
                    tipoVentaChecks.forEach(other => {
                        if (other !== this) other.checked = false;
                    });
                }
                syncTipoVentaHiddenInput();
            });
        });
    }

    syncTipoVentaHiddenInput();
    recalcularTotalesDesdeTabla();

    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-backdrop')) {
            cerrarModal();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            cerrarModal();
        }
    });

    ['efectivo', 'pos', 'transferencia'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', calcularVuelto);
        }
    });

    const tbody = document.getElementById("tablaProductos")?.querySelector("tbody");
    if (tbody) {
        tbody.addEventListener('input', function (e) {
            if (
                e.target.classList.contains('cantidad-producto-input') ||
                e.target.classList.contains('precio-unitario-input')
            ) {
                recalcularTotalesDesdeTabla();
            }
        });

        tbody.addEventListener('change', function (e) {
            if (
                e.target.classList.contains('cantidad-producto-input') ||
                e.target.classList.contains('precio-unitario-input')
            ) {
                recalcularTotalesDesdeTabla();
            }
        });
    }
});
