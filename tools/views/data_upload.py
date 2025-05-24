from django.shortcuts import render, redirect
from django.contrib import messages
from django.apps import apps
import pandas as pd
from io import StringIO
from tools.forms import DataUploadForm

def upload_csv(request):
    if request.method == 'POST':
        form = DataUploadForm(request.POST, request.FILES)
        
        if 'preview' in request.POST and form.is_valid():
            try:
                file = request.FILES['file']
                excel_info = None
                model = form.cleaned_data['model']
                
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    excel_file = pd.ExcelFile(file)
                    sheet_name = form.cleaned_data.get('sheet_name') or 0
                    cell_range = form.cleaned_data.get('cell_range')
                    
                    # Leer dimensiones primero para validación
                    full_df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    form.file_data = {
                        'max_col': len(full_df.columns),
                        'max_row': len(full_df)
                    }
                    
                    # Procesar con rango si fue especificado
                    df = process_excel_with_range(file, sheet_name, cell_range)
                    
                    excel_info = {
                        'available_sheets': excel_file.sheet_names,
                        'selected_sheet': sheet_name if isinstance(sheet_name, str) else excel_file.sheet_names[0],
                        'max_columns': len(full_df.columns)
                    }
                
                # Guardar el DataFrame en la sesión para confirmación posterior
                request.session['upload_data'] = {
                    'df_columns': df.columns.tolist(),
                    'df_rows': df.values.tolist(),
                    'model_path': f"{model._meta.app_label}.{model._meta.model_name}",
                    'clear_existing': form.cleaned_data['clear_existing'],
                    'file_type': 'csv' if file.name.endswith('.csv') else 'excel',
                    'excel_info': excel_info
                }
                
                context = {
                    'form': form,
                    'preview_mode': True,
                    'target_model': f"{model._meta.app_label}.{model._meta.model_name}",
                    'model_verbose_name': model._meta.verbose_name,
                    'df_info': {
                        'rows': len(df),
                        'columns': len(df.columns),
                        'missing_values': df.isnull().sum().sum(),
                        'column_types': {col: str(dtype) for col, dtype in df.dtypes.items()}
                    },
                    'df_preview': {
                        'columns': df.columns.tolist(),
                        'rows': df.head(10).values.tolist()
                    },
                    'excel_info': excel_info
                }
                return render(request, 'tools/upload_data_csv.html', context)
                
            except Exception as e:
                form.add_error(None, f"Error reading file: {str(e)}")


        elif 'confirm_upload' in request.POST:
            # Procesar la confirmación con los datos de la sesión
            upload_data = request.session.get('upload_data')
            if not upload_data:
                return redirect('data_upload')
            
            try:
                model = apps.get_model(upload_data['model_path'])
                df = pd.DataFrame(
                    data=upload_data['df_rows'],
                    columns=upload_data['df_columns']
                )
                
                # Configuración genérica de valores por defecto
                DEFAULT_VALUES = {
                    'CharField': '',
                    'IntegerField': 0,
                    'FloatField': 0.0,
                    'BooleanField': False,
                    'DateField': None,
                    'DateTimeField': None
                }
                
                # Obtener información de campos del modelo
                model_fields = {}
                for field in model._meta.get_fields():
                    if hasattr(field, 'get_internal_type'):
                        model_fields[field.name] = {
                            'type': field.get_internal_type(),
                            'null': field.null,
                            'blank': field.blank,
                            'default': field.default
                        }
                
                # Mapeo automático de columnas con nombres similares
                column_mapping = {}
                unused_columns = []
                
                for col in df.columns:
                    col_clean = col.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i')\
                                 .replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n').strip()
                    
                    best_match = None
                    best_score = 0
                    
                    for field in model_fields.keys():
                        field_clean = field.lower()
                        # Puntaje de similitud simple
                        score = sum(1 for a, b in zip(col_clean, field_clean) if a == b)
                        if score > best_score:
                            best_score = score
                            best_match = field
                    
                    if best_match and best_score >= max(3, len(best_match)/2):
                        column_mapping[col] = best_match
                    else:
                        unused_columns.append(col)
                
                # Mostrar advertencias para columnas no mapeadas
                if unused_columns:
                    messages.warning(request, 
                        f"Columnas no mapeadas: {', '.join(unused_columns)}. "
                        "Verifique los nombres de las columnas.")
                
                # Aquí va tu lógica para guardar en la base de datos
                if upload_data['clear_existing']:
                    model.objects.all().delete()
                
                # Crear objetos con manejo de valores nulos
                objs = []
                errors = []
                
                for idx, row in df.iterrows():
                    obj_data = {}
                    for col_name, value in row.items():
                        if col_name in column_mapping:
                            field_name = column_mapping[col_name]
                            field_info = model_fields[field_name]
                            
                            # Manejo de valores nulos
                            if pd.isna(value):
                                if field_info['default'] is not None:
                                    obj_data[field_name] = field_info['default']
                                elif field_info['null'] or field_info['blank']:
                                    obj_data[field_name] = None
                                else:
                                    default_value = DEFAULT_VALUES.get(field_info['type'])
                                    if default_value is not None:
                                        obj_data[field_name] = default_value
                                    else:
                                        errors.append(f"Fila {idx+1}: Campo '{field_name}' no puede ser nulo")
                                        continue
                            else:
                                obj_data[field_name] = value
                    
                    try:
                        objs.append(model(**obj_data))
                    except Exception as e:
                        errors.append(f"Fila {idx+1}: {str(e)}")
                        continue
                
                # Mostrar errores acumulados
                if errors:
                    for error in errors[:5]:  # Mostrar máximo 5 errores
                        messages.error(request, error)
                    if len(errors) > 5:
                        messages.error(request, f"... y {len(errors)-5} errores más")
                
                if objs:
                    model.objects.bulk_create(objs)
                    messages.success(request, f"Datos subidos exitosamente! {len(objs)} registros creados.")
                else:
                    messages.error(request, "No se crearon registros. Verifique los errores mostrados.")
                
                del request.session['upload_data']
                return redirect('dashboard')
                        
            except Exception as e:
                messages.error(request, f"Error subiendo datos: {str(e)}")
                return redirect('data_upload')



    else:
        form = DataUploadForm()
    
    return render(request, 'tools/upload_data_csv.html', {'form': form})

def process_excel_with_range(file, sheet_name, cell_range):
    """Procesa un archivo Excel con manejo seguro del rango especificado"""
    excel_file = pd.ExcelFile(file)
    
    try:
        # Si no hay rango especificado, devolver todo el sheet
        if not cell_range or not cell_range.strip():
            return pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Validar formato básico del rango
        if ':' not in cell_range:
            raise ValueError("El rango debe contener dos celdas separadas por ':' (ej. A1:B10)")
        
        # Extraer componentes del rango
        start, end = cell_range.split(':')
        
        # Función para extraer letras de columna
        def get_col_letters(s):
            letters = ''.join([c for c in str(s) if c.isalpha()])
            if not letters:
                raise ValueError(f"No se encontraron letras de columna en '{s}'")
            return letters.upper()
        
        # Función para extraer número de fila
        def get_row_number(s):
            digits = ''.join([c for c in str(s) if c.isdigit()])
            if not digits:
                raise ValueError(f"No se encontró número de fila en '{s}'")
            return int(digits)
        
        # Convertir letras de columna a índices (A=0, B=1, ...)
        def col_to_index(col_letters):
            index = 0
            for c in col_letters:
                if not c.isalpha():
                    raise ValueError(f"Carácter inválido en columna: '{c}'")
                index = index * 26 + (ord(c.upper()) - ord('A'))
            return index
        
        # Obtener componentes del rango
        start_col = get_col_letters(start)
        start_row = get_row_number(start) - 1  # Convertir a 0-based
        end_col = get_col_letters(end)
        end_row = get_row_number(end)  # Mantener 1-based
        
        # Convertir a índices
        start_col_idx = col_to_index(start_col)
        end_col_idx = col_to_index(end_col)
        
        # Leer todo el sheet
        full_df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        
        # Validar que los índices estén dentro de los límites
        max_cols = len(full_df.columns)
        max_rows = len(full_df)
        
        if start_col_idx >= max_cols or end_col_idx >= max_cols:
            available_cols = f"A-{chr(ord('A') + max_cols - 1)}" if max_cols <= 26 else f"A-ZZ"
            raise ValueError(f"Rango de columnas excede las disponibles ({available_cols})")
            
        if start_row >= max_rows or end_row > max_rows:
            raise ValueError(f"Rango de filas excede las disponibles (1-{max_rows})")
        
        # Extraer el rango especificado
        data = full_df.iloc[start_row:end_row, start_col_idx:end_col_idx+1]
        
        # Convertir a DataFrame (usando primera fila como headers si hay datos)
        if len(data) > 0:
            result_df = pd.DataFrame(data.values[1:], columns=data.iloc[0])
            return result_df
        return pd.DataFrame()
        
    except Exception as e:
        raise ValueError(f"Error procesando el archivo Excel: {str(e)}")