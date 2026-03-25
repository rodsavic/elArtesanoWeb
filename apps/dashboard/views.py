import csv
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, TruncYear
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.gastos.models import Gasto
from apps.ventas.models import Venta, VentaDetalle, VentaTipoDePago

def _obtener_rango_fechas(start_date, end_date):
    if not start_date or not end_date:
        today = timezone.now()
        return (
            today.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            today.replace(hour=23, minute=59, second=59, microsecond=999999),
        )

    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    return (
        timezone.make_aware(start_datetime.replace(hour=0, minute=0, second=0)),
        timezone.make_aware(end_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)),
    )


@login_required(login_url="/")
def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')


@login_required(login_url="/")
def dashboard_data_api(request):
    try:
        period = request.GET.get('period', 'month')
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        start_dt, end_dt = _obtener_rango_fechas(start_date, end_date)

        ventas_queryset = Venta.objects.filter(fecha_venta__range=(start_dt, end_dt))
        gastos_queryset = Gasto.objects.filter(fecha_gasto__range=(start_dt.date(), end_dt.date()))

        summary_data = ventas_queryset.aggregate(
            total_sales=Sum('total_venta'),
            sales_count=Count('id_venta'),
            total_iva_10=Sum('total_iva_10'),
            total_iva_5=Sum('total_iva_5'),
        )
        total_sales = float(summary_data['total_sales'] or 0)
        total_expenses = float(gastos_queryset.aggregate(total=Sum('monto'))['total'] or 0)

        return JsonResponse({
            'summary': {
                'totalSales': total_sales,
                'salesCount': summary_data['sales_count'] or 0,
                'totalIVA10': float(summary_data['total_iva_10'] or 0),
                'totalIVA5': float(summary_data['total_iva_5'] or 0),
                'totalExpenses': total_expenses,
                'netBalance': total_sales - total_expenses,
            },
            'salesByPeriod': get_sales_by_period(ventas_queryset, period),
            'expensesByPeriod': get_expenses_by_period(gastos_queryset, period),
            'paymentTypes': get_payment_types_data(ventas_queryset),
        })
    except Exception as error:
        return JsonResponse({'error': str(error)}, status=500)


def get_sales_by_period(queryset, period):
    if period == 'day':
        data = queryset.annotate(day=TruncDate('fecha_venta')).values('day').annotate(total=Sum('total_venta')).order_by('day')
        day_names = {0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue', 4: 'Vie', 5: 'Sáb', 6: 'Dom'}
        labels = [f"{day_names[item['day'].weekday()]} {item['day'].strftime('%d/%m')}" for item in data if item['day']]
        values = [float(item['total'] or 0) for item in data if item['day']]
    elif period == 'week':
        data = queryset.annotate(week=TruncWeek('fecha_venta')).values('week').annotate(total=Sum('total_venta')).order_by('week')
        labels = [f"Sem {item['week'].strftime('%W')} ({item['week'].strftime('%d/%m')})" for item in data if item['week']]
        values = [float(item['total'] or 0) for item in data if item['week']]
    elif period == 'month':
        data = queryset.annotate(month=TruncMonth('fecha_venta')).values('month').annotate(total=Sum('total_venta')).order_by('month')
        month_names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        labels = [f"{month_names[item['month'].month - 1]} {item['month'].year}" for item in data if item['month']]
        values = [float(item['total'] or 0) for item in data if item['month']]
    else:
        data = queryset.annotate(year=TruncYear('fecha_venta')).values('year').annotate(total=Sum('total_venta')).order_by('year')
        labels = [str(item['year'].year) for item in data if item['year']]
        values = [float(item['total'] or 0) for item in data if item['year']]

    return {'labels': labels, 'data': values}


def get_expenses_by_period(queryset, period):
    if period == 'day':
        data = queryset.annotate(day=TruncDate('fecha_gasto')).values('day').annotate(total=Sum('monto')).order_by('day')
        day_names = {0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue', 4: 'Vie', 5: 'Sáb', 6: 'Dom'}
        labels = [f"{day_names[item['day'].weekday()]} {item['day'].strftime('%d/%m')}" for item in data if item['day']]
        values = [float(item['total'] or 0) for item in data if item['day']]
    elif period == 'week':
        data = queryset.annotate(week=TruncWeek('fecha_gasto')).values('week').annotate(total=Sum('monto')).order_by('week')
        labels = [f"Sem {item['week'].strftime('%W')} ({item['week'].strftime('%d/%m')})" for item in data if item['week']]
        values = [float(item['total'] or 0) for item in data if item['week']]
    elif period == 'month':
        data = queryset.annotate(month=TruncMonth('fecha_gasto')).values('month').annotate(total=Sum('monto')).order_by('month')
        month_names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        labels = [f"{month_names[item['month'].month - 1]} {item['month'].year}" for item in data if item['month']]
        values = [float(item['total'] or 0) for item in data if item['month']]
    else:
        data = queryset.annotate(year=TruncYear('fecha_gasto')).values('year').annotate(total=Sum('monto')).order_by('year')
        labels = [str(item['year'].year) for item in data if item['year']]
        values = [float(item['total'] or 0) for item in data if item['year']]

    return {'labels': labels, 'data': values}


def get_payment_types_data(queryset):
    venta_ids = queryset.values_list('id_venta', flat=True)
    payment_data = VentaTipoDePago.objects.filter(id_venta__in=venta_ids).select_related('id_tipo_pago').values(
        'id_tipo_pago__descripcion'
    ).annotate(total=Sum('monto')).order_by('-total')

    labels = []
    data = []
    colors_palette = ['#8b5e3c', '#b7815a', '#d7b59a', '#6f4a2f', '#4b3425']
    for index, item in enumerate(payment_data):
        labels.append(item['id_tipo_pago__descripcion'] or f'Tipo {index + 1}')
        data.append(float(item['total'] or 0))

    return {'labels': labels, 'data': data, 'colors': colors_palette[:len(labels)]}


@login_required(login_url="/")
def daily_report_view(request):
    try:
        report_date = request.GET.get('date')
        if report_date:
            report_datetime = datetime.strptime(report_date, '%Y-%m-%d')
            start_dt = timezone.make_aware(report_datetime.replace(hour=0, minute=0, second=0))
            end_dt = timezone.make_aware(report_datetime.replace(hour=23, minute=59, second=59, microsecond=999999))
        else:
            today = timezone.now()
            start_dt = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            report_date = today.strftime('%Y-%m-%d')

        ventas = Venta.objects.filter(
            fecha_venta__gte=start_dt,
            fecha_venta__lte=end_dt
        ).select_related('id_cliente').prefetch_related(
            'ventadetalle_set__id_producto',
            'ventatipodepago_set__id_tipo_pago'
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{report_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID Venta', 'Fecha', 'Cliente', 'Total Venta', 'IVA 10%', 'IVA 5%', 'Productos', 'Tipos de Pago'])

        for venta in ventas:
            productos_str = ' | '.join([
                f"{detalle.id_producto.nombre} (Cant: {detalle.cantidad_producto}, Total: Gs {detalle.total_detalle:,.0f})"
                for detalle in venta.ventadetalle_set.all()
            ])
            tipos_pago_str = ' | '.join([
                f"{pago.id_tipo_pago.descripcion}: Gs {pago.monto:,.0f}"
                for pago in venta.ventatipodepago_set.all()
            ])
            writer.writerow([
                venta.id_venta,
                venta.fecha_venta.strftime('%d/%m/%Y %H:%M'),
                str(venta.id_cliente),
                f"Gs {venta.total_venta:,.0f}",
                f"Gs {venta.total_iva_10:,.0f}",
                f"Gs {venta.total_iva_5:,.0f}",
                productos_str,
                tipos_pago_str
            ])
        return response
    except Exception as error:
        return JsonResponse({'error': str(error)}, status=500)


@login_required(login_url="/")
def daily_report_pdf_view(request):
    try:
        report_date = request.GET.get('date')
        if report_date:
            report_datetime = datetime.strptime(report_date, '%Y-%m-%d')
            start_dt = timezone.make_aware(report_datetime.replace(hour=0, minute=0, second=0))
            end_dt = timezone.make_aware(report_datetime.replace(hour=23, minute=59, second=59, microsecond=999999))
            report_date_str = report_datetime.strftime('%d/%m/%Y')
        else:
            today = timezone.now()
            start_dt = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            report_date = today.strftime('%Y-%m-%d')
            report_date_str = today.strftime('%d/%m/%Y')

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{report_date}.pdf"'
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f"<b>Reporte Diario de Ventas - {report_date_str}</b>", styles['Title']))
        elements.append(Spacer(1, 20))

        ventas = Venta.objects.filter(
            fecha_venta__gte=start_dt,
            fecha_venta__lte=end_dt
        ).select_related('id_cliente')

        if not ventas.exists():
            elements.append(Paragraph("No se encontraron ventas para esta fecha.", styles['Normal']))
        else:
            totals = ventas.aggregate(
                total_ventas=Sum('total_venta'),
                total_iva_10=Sum('total_iva_10'),
                total_iva_5=Sum('total_iva_5'),
                count_ventas=Count('id_venta')
            )

            summary_data = [
                ['Concepto', 'Valor'],
                ['Total de Ventas', f"Gs {totals['total_ventas']:,.0f}"],
                ['Cantidad de Ventas', f"{totals['count_ventas']}"],
                ['Total IVA 10%', f"Gs {totals['total_iva_10']:,.0f}"],
                ['Total IVA 5%', f"Gs {totals['total_iva_5']:,.0f}"]
            ]
            summary_table = Table(summary_data, colWidths=[170, 170])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 30))

            detail_title = Paragraph("<b>Detalle de Ventas</b>", styles['Heading2'])
            elements.append(detail_title)
            elements.append(Spacer(1, 10))

            table_data = [['ID', 'Hora', 'Cliente', 'Total', 'IVA 10%', 'IVA 5%']]
            for venta in ventas:
                table_data.append([
                    str(venta.id_venta),
                    venta.fecha_venta.strftime('%H:%M'),
                    str(venta.id_cliente),
                    f"Gs {venta.total_venta:,.0f}",
                    f"Gs {venta.total_iva_10:,.0f}",
                    f"Gs {venta.total_iva_5:,.0f}"
                ])

            detail_table = Table(table_data, colWidths=[55, 55, 110, 95, 80, 80])
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(detail_table)

        doc.build(elements)
        return response
    except Exception as error:
        return JsonResponse({'error': str(error)}, status=500)


@login_required(login_url="/")
def top_products_api(request):
    try:
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        limit = int(request.GET.get('limit', 10))
        start_dt, end_dt = _obtener_rango_fechas(start_date, end_date)

        top_products = VentaDetalle.objects.filter(
            id_venta__fecha_venta__gte=start_dt,
            id_venta__fecha_venta__lte=end_dt
        ).select_related('id_producto').values(
            'id_producto__nombre'
        ).annotate(
            total_cantidad=Sum('cantidad_producto'),
            total_ventas=Sum('total_detalle')
        ).order_by('-total_cantidad')[:limit]

        products_data = [{
            'nombre': item['id_producto__nombre'],
            'cantidad': float(item['total_cantidad']),
            'ventas': float(item['total_ventas'])
        } for item in top_products]

        return JsonResponse({'products': products_data})
    except Exception as error:
        return JsonResponse({'error': str(error)}, status=500)


@login_required(login_url="/")
def customer_stats_api(request):
    try:
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        start_dt, end_dt = _obtener_rango_fechas(start_date, end_date)

        customer_stats = Venta.objects.filter(
            fecha_venta__gte=start_dt,
            fecha_venta__lte=end_dt
        ).select_related('id_cliente').values(
            'id_cliente__nombre'
        ).annotate(
            total_compras=Sum('total_venta'),
            cantidad_compras=Count('id_venta')
        ).order_by('-total_compras')[:10]

        customers_data = [{
            'nombre': item['id_cliente__nombre'],
            'total_compras': float(item['total_compras']),
            'cantidad_compras': item['cantidad_compras']
        } for item in customer_stats]

        return JsonResponse({'customers': customers_data})
    except Exception as error:
        return JsonResponse({'error': str(error)}, status=500)
