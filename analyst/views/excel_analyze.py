# analyst/views/excel_analyze.py
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from analyst.services.excel_analyzer import ExcelRangeAnalyzer

logger = logging.getLogger(__name__)


@require_POST
def analyze_excel_ajax(request):
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo'}, status=400)

    file_obj   = request.FILES['file']
    sheet_name = request.POST.get('sheet_name', '').strip()

    if not (file_obj.name.lower().endswith('.xlsx') or file_obj.name.lower().endswith('.xls')):
        return JsonResponse({'success': False, 'error': 'Solo se admiten .xlsx o .xls'}, status=400)

    try:
        if not sheet_name:
            result = ExcelRangeAnalyzer.get_sheets(file_obj)
            if result['error']:
                return JsonResponse({'success': False, 'error': result['error']}, status=400)
            return JsonResponse({'success': True, 'mode': 'sheets', 'sheets': result['sheets']})
        else:
            result = ExcelRangeAnalyzer.analyze_sheet(file_obj, sheet_name)
            if result.get('error'):
                return JsonResponse({'success': False, 'error': result['error']}, status=400)
            return JsonResponse({
                'success':      True,
                'mode':         'analysis',
                'sheet':        result['sheet'],
                'max_row':      result['max_row'],
                'max_col':      result['max_col'],
                'regions':      result['regions'],
                'merge_groups': result['merge_groups'],   # ← nuevo
                'recommended':  result['recommended'],
                'multi':        result['multi'],
            })
    except Exception as e:
        logger.error(f"Error en analyze_excel_ajax: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
