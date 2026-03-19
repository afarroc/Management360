# analyst/urls.py
from django.urls import path
from analyst.views import (
    data_upload, clipboard, file_views, other_tools, excel_analyze,
    data_upload_async,
    dataset_manager,
    report_builder,
    etl_manager,
    analyst_base,
    cross_source,
    dashboard,
    docs,
    pipeline,
)
app_name = 'analyst'

urlpatterns = [

    # ── Upload panel ─────────────────────────────────────────────────────────
    path('upload/',                 data_upload.upload_csv,                    name='data_upload'),

    # Async upload/edit (SPA endpoints, return JSON)
    path('upload/preview/',         data_upload_async.preview_async,           name='preview_async'),
    path('upload/preview-page/',    data_upload_async.preview_page_async,      name='preview_page_async'),
    path('upload/confirm/',         data_upload_async.confirm_upload_async,    name='confirm_upload_async'),
    path('edit/delete-columns/',    data_upload_async.delete_columns_async,    name='delete_columns_async'),
    path('edit/replace-values/',    data_upload_async.replace_values_async,    name='replace_values_async'),
    path('edit/fill-na/',           data_upload_async.fill_na_async,           name='fill_na_async'),
    path('edit/convert-date/',      data_upload_async.convert_date_async,      name='convert_date_async'),
    path('edit/rename-column/',     data_upload_async.rename_column_async,     name='rename_column_async'),
    path('edit/drop-duplicates/',   data_upload_async.drop_duplicates_async,   name='drop_duplicates_async'),
    path('edit/sort-data/',         data_upload_async.sort_data_async,         name='sort_data_async'),
    path('edit/convert-dtype/',     data_upload_async.convert_dtype_async,     name='convert_dtype_async'),
    path('edit/normalize-text/',    data_upload_async.normalize_text_async,    name='normalize_text_async'),
    path('edit/filter-count/',      data_upload_async.filter_rows_count_async,  name='filter_rows_count_async'),
    path('edit/filter-delete/',     data_upload_async.filter_rows_delete_async, name='filter_rows_delete_async'),
    path('edit/filter-replace/',    data_upload_async.filter_rows_replace_async, name='filter_rows_replace_async'),
    path('edit/unique-values/',     data_upload_async.filter_unique_values_async, name='filter_unique_values_async'),
    path('edit/apply-defaults/',    data_upload_async.apply_field_defaults_async, name='apply_field_defaults_async'),
    path('clipboard/save-async/',   data_upload_async.save_clipboard_async,    name='save_clipboard_async'),
    path('clipboard/load-preview/', data_upload_async.load_clip_as_preview,    name='load_clip_as_preview'),
    path('upload/save-as-dataset/',  data_upload_async.save_as_dataset,          name='save_as_dataset'),
    path('upload/reanalyze/',           data_upload_async.reanalyze_async,          name='reanalyze_async'),

    # Legacy AJAX endpoints (kept for backward compat)
    path('clipboard/save/',         data_upload.save_clipboard_ajax,           name='save_clipboard_ajax'),
    path('clipboard/load-data/',    data_upload.load_clipboard_data,           name='load_clipboard_data'),

    # ── Clipboard ────────────────────────────────────────────────────────────
    path('clipboard/details/',          clipboard.clipboard_details,           name='clipboard_details'),
    path('clipboard/export-csv/',       clipboard.export_clipboard_csv,        name='export_clipboard_csv'),
    path('clipboard/list/',             clipboard.clipboard_list,              name='clipboard_list'),
    path('clipboard/load-form/',        clipboard.load_clipboard_form,         name='load_clipboard_form'),
    path('clipboard/load-form-data/',   clipboard.load_clipboard_form_data,    name='load_clipboard_form_data'),
    path('clipboard/delete/',           data_upload.delete_clip_ajax,          name='delete_clip_ajax'),
    path('clipboard/clear-all/',        data_upload.clear_all_clips_ajax,      name='clear_all_clips_ajax'),

    # ── Stored Datasets ──────────────────────────────────────────────────────
    path('datasets/',                       dataset_manager.dataset_list,      name='dataset_list'),
    path('datasets/save/',                  dataset_manager.dataset_save,      name='dataset_save'),
    path('datasets/api/columns/',           dataset_manager.dataset_columns_api, name='dataset_columns_api'),
    path('datasets/<uuid:dataset_id>/delete/',  dataset_manager.dataset_delete,  name='dataset_delete'),
    path('datasets/<uuid:dataset_id>/preview/', dataset_manager.dataset_preview, name='dataset_preview'),
    path('datasets/<uuid:dataset_id>/export/', dataset_manager.dataset_export,   name='dataset_export'),

    # ── Report Builder ───────────────────────────────────────────────────────
    path('reports/',                        report_builder.report_list,        name='report_list'),
    path('reports/build/',                  report_builder.report_build,       name='report_build'),
    path('reports/api/functions/',          report_builder.functions_api,      name='functions_api'),
    path('reports/<uuid:report_id>/detail/', report_builder.report_detail,     name='report_detail'),
    path('reports/<uuid:report_id>/delete/', report_builder.report_delete,     name='report_delete'),
    path('reports/<uuid:report_id>/export/', report_builder.report_export,     name='report_export'),
    path('reports/<uuid:report_id>/rerun/',  report_builder.report_rerun,      name='report_rerun'),

    # ── File management ──────────────────────────────────────────────────────
    path('file-tree/',          file_views.file_tree_view,                     name='file_tree'),

    # ── Other tools ──────────────────────────────────────────────────────────
    path('calculate-agents/',   other_tools.calculate_agents,                  name='calculate_agents'),
    path('traffic-intensity/',  other_tools.calcular_trafico_intensidad_view,  name='traffic_intensity'),

    # ── Excel analyzer ───────────────────────────────────────────────────────
    path('excel/analyze/',      excel_analyze.analyze_excel_ajax,              name='analyze_excel'),

    # ── ETL ──────────────────────────────────────────────────────────────────
    path('etl/',                             etl_manager.etl_list,             name='etl_list'),
    path('etl/sources/save/',                etl_manager.etl_source_save,      name='etl_source_save'),
    path('etl/sources/<uuid:source_id>/delete/', etl_manager.etl_source_delete, name='etl_source_delete'),
    path('etl/sources/<uuid:source_id>/run/', etl_manager.etl_source_run,      name='etl_source_run'),
    path('etl/jobs/<uuid:job_id>/status/',   etl_manager.etl_job_status,       name='etl_job_status'),
    path('etl/api/models/',                  etl_manager.etl_models_api,       name='etl_models_api'),
    path('etl/api/model-fields/',            etl_manager.etl_model_fields_api, name='etl_model_fields_api'),

# ─────────────────────────────────────────────────────────────────────────────
# AGREGAR a analyst/urls.py
# 1. Import:  from analyst.views import analyst_base
# 2. Pegar en urlpatterns:
# ─────────────────────────────────────────────────────────────────────────────

    path('bases/',                                     analyst_base.base_list,            name='base_list'),
    path('bases/create/',                              analyst_base.base_create,           name='base_create'),
    path('bases/api/',                                 analyst_base.bases_api,             name='bases_api'),
    path('bases/sources/',                             analyst_base.sources_api,           name='bases_sources_api'),
    path('bases/sources/columns-from-clip/',           analyst_base.clip_columns_api,      name='clip_columns_api'),
    path('bases/<uuid:base_id>/schema/',               analyst_base.base_schema_update,    name='base_schema_update'),
    path('bases/<uuid:base_id>/delete/',               analyst_base.base_delete,           name='base_delete'),
    path('bases/<uuid:base_id>/data/',                 analyst_base.base_data,             name='base_data'),
    path('bases/<uuid:base_id>/rows/add/',             analyst_base.base_row_add,          name='base_row_add'),
    path('bases/<uuid:base_id>/rows/edit/',            analyst_base.base_row_edit,         name='base_row_edit'),
    path('bases/<uuid:base_id>/rows/delete/',          analyst_base.base_row_delete,       name='base_row_delete'),
    path('bases/<uuid:base_id>/bulk-import/',          analyst_base.base_bulk_import,      name='base_bulk_import'),
    path('bases/<uuid:base_id>/bulk-import-raw/',      analyst_base.base_bulk_import_raw,  name='base_bulk_import_raw'),
    path('bases/<uuid:base_id>/export/',               analyst_base.base_export,           name='base_export'),
    path('bases/<uuid:base_id>/columns/',              analyst_base.base_columns_api,      name='base_columns_api'),
# ─────────────────────────────────────────────────────────────────────────────
# AGREGAR a analyst/urls.py — Fase 2: CrossSource
#
# 1. En el bloque de imports, agregar:
#       from analyst.views import cross_source
#
# 2. En urlpatterns, agregar:
# ─────────────────────────────────────────────────────────────────────────────

    # ── CrossSource ──────────────────────────────────────────────────────────
    path('cross/',                                cross_source.cross_list,         name='cross_list'),
    path('cross/create/',                         cross_source.cross_create,       name='cross_create'),
    path('cross/api/',                            cross_source.crosses_api,        name='crosses_api'),
    path('cross/api/columns/',                    cross_source.cross_columns_api,  name='cross_columns_api'),
    path('cross/<uuid:cross_id>/update/',         cross_source.cross_update,       name='cross_update'),
    path('cross/<uuid:cross_id>/run/',            cross_source.cross_run,          name='cross_run'),
    path('cross/<uuid:cross_id>/delete/',         cross_source.cross_delete,       name='cross_delete'),
    path('cross/<uuid:cross_id>/preview/',        cross_source.cross_preview,      name='cross_preview'),


    # ── Dashboards ───────────────────────────────────────────────────────────────
    path('dashboards/',                                          dashboard.dashboard_list,        name='dashboard_list'),
    path('dashboards/create/',                                   dashboard.dashboard_create,      name='dashboard_create'),
    path('dashboards/<uuid:dashboard_id>/view/',                 dashboard.dashboard_view,        name='dashboard_view'),
    path('dashboards/<uuid:dashboard_id>/update/',               dashboard.dashboard_update,      name='dashboard_update'),
    path('dashboards/<uuid:dashboard_id>/delete/',               dashboard.dashboard_delete,      name='dashboard_delete'),
    path('dashboards/<uuid:dashboard_id>/layout/save/',          dashboard.dashboard_layout_save, name='dashboard_layout_save'),
    path('dashboards/<uuid:dashboard_id>/widgets/add/',          dashboard.widget_add,            name='widget_add'),
    path('dashboards/<uuid:dashboard_id>/widgets/<uuid:widget_id>/update/', dashboard.widget_update, name='widget_update'),
    path('dashboards/<uuid:dashboard_id>/widgets/<uuid:widget_id>/delete/', dashboard.widget_delete, name='widget_delete'),
    path('dashboards/<uuid:dashboard_id>/widgets/<uuid:widget_id>/data/',   dashboard.widget_data,   name='widget_data'),

    # ── Pipelines ────────────────────────────────────────────────────────────────
    path('pipelines/',                                       pipeline.pipeline_list,   name='pipeline_list'),
    path('pipelines/api/',                                   pipeline.pipeline_api,    name='pipeline_api'),
    path('pipelines/create/',                                pipeline.pipeline_create, name='pipeline_create'),
    path('pipelines/<uuid:pipeline_id>/update/',             pipeline.pipeline_update, name='pipeline_update'),
    path('pipelines/<uuid:pipeline_id>/delete/',             pipeline.pipeline_delete, name='pipeline_delete'),
    path('pipelines/<uuid:pipeline_id>/steps/add/',          pipeline.step_add,        name='pipeline_step_add'),
    path('pipelines/<uuid:pipeline_id>/steps/reorder/',      pipeline.step_reorder,    name='pipeline_step_reorder'),
    path('pipelines/<uuid:pipeline_id>/steps/<int:step_index>/delete/', pipeline.step_delete, name='pipeline_step_delete'),
    path('pipelines/<uuid:pipeline_id>/run/',                pipeline.pipeline_run,    name='pipeline_run'),
    path('pipelines/<uuid:pipeline_id>/runs/',               pipeline.pipeline_runs,   name='pipeline_runs'),

    # ── Docs ─────────────────────────────────────────────────────────────────────
    path('docs/<str:doc_key>/', docs.docs_view, name='docs'),

]
