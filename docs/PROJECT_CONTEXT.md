# Mapa del Proyecto — Management360

> Generado por `m360_map.sh`  |  2026-03-20 18:52:19
> Raíz: `/data/data/com.termux/files/home/projects/Management360`
> Apps: **20**  |  Archivos Python+HTML: **713**

---

## Resumen por app

| App | Namespace | Archivos | Modelos | Endpoints | Notas |
|-----|-----------|----------|---------|-----------|-------|
| `accounts` | `—` | 19 | 1 | 11 | Autenticacion, Perfiles, CV |
| `analyst` | `analyst` | 59 | 10 | 99 | Plataforma de datos (5 fases, SIM-4 integrado) |
| `api` | `—` | 6 | 00 | 4 | API REST publica |
| `bitacora` | `bitacora` | 17 | 4 | 9 | Bitacora personal GTD |
| `board` | `board` | 15 | 3 | 8 | Kanban board |
| `bots` | `bots` | 16 | 10 | 13 | Automatizaciones, bots |
| `campaigns` | `campaigns` | 6 | 3 | 6 | Campanas, outreach |
| `chat` | `chat` | 27 | 6 | 40 | Chat en tiempo real, rooms, mensajes |
| `core` | `—` | 44 | 1 | 16 | Dashboard, URL-map, Home |
| `courses` | `courses` | 88 | 12 | 59 | Cursos, lecciones, curriculum |
| `cv` | `cv` | 32 | 10 | 14 | Curriculum Vitae dinamico |
| `events` | `events` | 233 | 31 | 147 | Eventos, Proyectos, Tareas (app principal) |
| `help` | `help` | 15 | 7 | 10 | Centro de ayuda, tickets |
| `kpis` | `kpis` | 11 | 2 | 5 | KPIs, AHT Dashboard, CallRecord |
| `memento` | `—` | 16 | 1 | 6 | Recordatorios, memoria personal |
| `panel` | `—` | 9 | 0 | 28 | Panel de configuracion del proyecto |
| `passgen` | `—` | 12 | 00 | 2 | Generador de contrasenas |
| `rooms` | `rooms` | 46 | 16 | 53 | Salas virtuales, channels |
| `sim` | `sim` | 33 | 11 | 48 | Simulador WFM — SIM-1→SIM-7a completo (ACD multi-agente) |
| `simcity` | `simcity` | 9 | 1 | 14 |  |

---

## Árbol del Proyecto (nivel 1)

```
Management360/
    ├── .backup_20260317_124217/
    ├── .django_cache/
    ├── accounts/
    ├── analyst/
    ├── api/
    ├── bitacora/
    ├── board/
    ├── bots/
    ├── campaigns/
    ├── chat/
    ├── core/
    ├── courses/
    ├── cv/
    ├── docs/
    ├── events/
    ├── gtd_setup/
    ├── help/
    ├── kpis/
    ├── memento/
    ├── panel/
    ├── passgen/
    ├── rooms/
    ├── scripts/
    ├── services/
    ├── sim/
    ├── simcity/
    ├── staticfiles/
    ├── ACCOUNTS_CONTEXT.md
    ├── API_CONTEXT.md
    ├── BOARD_CONTEXT.md
    ├── CAMPAIGNS_CONTEXT.md
    ├── CHAT_CONTEXT.md
    ├── CORE_CONTEXT.md
    ├── COURSES_CONTEXT.md
    ├── CV_CONTEXT.md
    ├── EVENTS_CONTEXT.md
    ├── HELP_CONTEXT.md
    ├── KPIS_CONTEXT.md
    ├── MEMENTO_CONTEXT.md
    ├── PANEL_CONTEXT.md
    ├── PASSGEN_CONTEXT.md
    ├── README.md
    ├── ROOMS_CONTEXT.md
    ├── _fix_git_ignore.py
    ├── build.sh
    ├── create_gtd_structure.sh
    └── manage.py
```

---

## URLs por app

> Equivalente a la vista `/url-map/` del sistema (core/utils.py::get_all_apps_url_structure)

### `accounts` — namespace: `accounts`

| Pattern | Name |
|---------|------|
| `/accounts/signup/` | `signup` |
| `/accounts/login/` | `login` |
| `/accounts/logout/` | `logout` |

### `analyst` — namespace: `analyst`

| Pattern | Name |
|---------|------|
| `/analyst/upload/` | `data_upload` |
| `/analyst/upload/preview/` | `preview_async` |
| `/analyst/upload/preview-page/` | `preview_page_async` |
| `/analyst/upload/confirm/` | `confirm_upload_async` |
| `/analyst/edit/delete-columns/` | `delete_columns_async` |
| `/analyst/edit/replace-values/` | `replace_values_async` |
| `/analyst/edit/fill-na/` | `fill_na_async` |
| `/analyst/edit/convert-date/` | `convert_date_async` |
| `/analyst/edit/rename-column/` | `rename_column_async` |
| `/analyst/edit/drop-duplicates/` | `drop_duplicates_async` |
| `/analyst/edit/sort-data/` | `sort_data_async` |
| `/analyst/edit/convert-dtype/` | `convert_dtype_async` |
| `/analyst/edit/normalize-text/` | `normalize_text_async` |
| `/analyst/edit/filter-count/` | `filter_rows_count_async` |
| `/analyst/edit/filter-delete/` | `filter_rows_delete_async` |
| `/analyst/edit/filter-replace/` | `filter_rows_replace_async` |
| `/analyst/edit/unique-values/` | `filter_unique_values_async` |
| `/analyst/edit/apply-defaults/` | `apply_field_defaults_async` |
| `/analyst/clipboard/save-async/` | `save_clipboard_async` |
| `/analyst/clipboard/load-preview/` | `load_clip_as_preview` |
| `/analyst/upload/save-as-dataset/` | `save_as_dataset` |
| `/analyst/upload/reanalyze/` | `reanalyze_async` |
| `/analyst/clipboard/save/` | `save_clipboard_ajax` |
| `/analyst/clipboard/load-data/` | `load_clipboard_data` |
| `/analyst/clipboard/details/` | `clipboard_details` |
| `/analyst/clipboard/export-csv/` | `export_clipboard_csv` |
| `/analyst/clipboard/list/` | `clipboard_list` |
| `/analyst/clipboard/load-form/` | `load_clipboard_form` |
| `/analyst/clipboard/load-form-data/` | `load_clipboard_form_data` |
| `/analyst/clipboard/delete/` | `delete_clip_ajax` |
| `/analyst/clipboard/clear-all/` | `clear_all_clips_ajax` |
| `/analyst/datasets/` | `dataset_list` |
| `/analyst/datasets/save/` | `dataset_save` |
| `/analyst/datasets/api/columns/` | `dataset_columns_api` |
| `/analyst/datasets/<uuid:dataset_id>/delete/` | `dataset_delete` |
| `/analyst/datasets/<uuid:dataset_id>/preview/` | `dataset_preview` |
| `/analyst/datasets/<uuid:dataset_id>/export/` | `dataset_export` |
| `/analyst/reports/` | `report_list` |
| `/analyst/reports/build/` | `report_build` |
| `/analyst/reports/api/functions/` | `functions_api` |
| `/analyst/reports/<uuid:report_id>/detail/` | `report_detail` |
| `/analyst/reports/<uuid:report_id>/delete/` | `report_delete` |
| `/analyst/reports/<uuid:report_id>/export/` | `report_export` |
| `/analyst/reports/<uuid:report_id>/rerun/` | `report_rerun` |
| `/analyst/file-tree/` | `file_tree` |
| `/analyst/calculate-agents/` | `calculate_agents` |
| `/analyst/traffic-intensity/` | `traffic_intensity` |
| `/analyst/excel/analyze/` | `analyze_excel` |
| `/analyst/etl/` | `etl_list` |
| `/analyst/etl/sources/save/` | `etl_source_save` |
| `/analyst/etl/sources/<uuid:source_id>/delete/` | `etl_source_delete` |
| `/analyst/etl/sources/<uuid:source_id>/run/` | `etl_source_run` |
| `/analyst/etl/jobs/<uuid:job_id>/status/` | `etl_job_status` |
| `/analyst/etl/api/models/` | `etl_models_api` |
| `/analyst/etl/api/model-fields/` | `etl_model_fields_api` |
| `/analyst/bases/` | `base_list` |
| `/analyst/bases/create/` | `base_create` |
| `/analyst/bases/api/` | `bases_api` |
| `/analyst/bases/sources/` | `bases_sources_api` |
| `/analyst/bases/sources/columns-from-clip/` | `clip_columns_api` |
| `/analyst/bases/<uuid:base_id>/schema/` | `base_schema_update` |
| `/analyst/bases/<uuid:base_id>/delete/` | `base_delete` |
| `/analyst/bases/<uuid:base_id>/data/` | `base_data` |
| `/analyst/bases/<uuid:base_id>/rows/add/` | `base_row_add` |
| `/analyst/bases/<uuid:base_id>/rows/edit/` | `base_row_edit` |
| `/analyst/bases/<uuid:base_id>/rows/delete/` | `base_row_delete` |
| `/analyst/bases/<uuid:base_id>/bulk-import/` | `base_bulk_import` |
| `/analyst/bases/<uuid:base_id>/bulk-import-raw/` | `base_bulk_import_raw` |
| `/analyst/bases/<uuid:base_id>/export/` | `base_export` |
| `/analyst/bases/<uuid:base_id>/columns/` | `base_columns_api` |
| `/analyst/cross/` | `cross_list` |
| `/analyst/cross/create/` | `cross_create` |
| `/analyst/cross/api/` | `crosses_api` |
| `/analyst/cross/api/columns/` | `cross_columns_api` |
| `/analyst/cross/<uuid:cross_id>/update/` | `cross_update` |
| `/analyst/cross/<uuid:cross_id>/run/` | `cross_run` |
| `/analyst/cross/<uuid:cross_id>/delete/` | `cross_delete` |
| `/analyst/cross/<uuid:cross_id>/preview/` | `cross_preview` |
| `/analyst/dashboards/` | `dashboard_list` |
| `/analyst/dashboards/create/` | `dashboard_create` |
| `/analyst/dashboards/<uuid:dashboard_id>/view/` | `dashboard_view` |
| `/analyst/dashboards/<uuid:dashboard_id>/update/` | `dashboard_update` |
| `/analyst/dashboards/<uuid:dashboard_id>/delete/` | `dashboard_delete` |
| `/analyst/dashboards/<uuid:dashboard_id>/layout/save/` | `dashboard_layout_save` |
| `/analyst/dashboards/<uuid:dashboard_id>/widgets/add/` | `widget_add` |
| `/analyst/dashboards/<uuid:dashboard_id>/widgets/<uuid:widget_id>/update/` | `widget_update` |
| `/analyst/dashboards/<uuid:dashboard_id>/widgets/<uuid:widget_id>/delete/` | `widget_delete` |
| `/analyst/dashboards/<uuid:dashboard_id>/widgets/<uuid:widget_id>/data/` | `widget_data` |
| `/analyst/pipelines/` | `pipeline_list` |
| `/analyst/pipelines/api/` | `pipeline_api` |
| `/analyst/pipelines/create/` | `pipeline_create` |
| `/analyst/pipelines/<uuid:pipeline_id>/update/` | `pipeline_update` |
| `/analyst/pipelines/<uuid:pipeline_id>/delete/` | `pipeline_delete` |
| `/analyst/pipelines/<uuid:pipeline_id>/steps/add/` | `pipeline_step_add` |
| `/analyst/pipelines/<uuid:pipeline_id>/steps/reorder/` | `pipeline_step_reorder` |
| `/analyst/pipelines/<uuid:pipeline_id>/steps/<int:step_index>/delete/` | `pipeline_step_delete` |
| `/analyst/pipelines/<uuid:pipeline_id>/run/` | `pipeline_run` |
| `/analyst/pipelines/<uuid:pipeline_id>/runs/` | `pipeline_runs` |
| `/analyst/docs/<str:doc_key>/` | `docs` |

### `api` — namespace: `api`

| Pattern | Name |
|---------|------|
| `/api/csrf/` | `api-csrf` |
| `/api/login/` | `api-login` |
| `/api/logout/` | `api-logout` |
| `/api/signup/` | `api-signup` |

### `bitacora` — namespace: `bitacora`

| Pattern | Name |
|---------|------|
| `/bitacora/list/` | `bitacora/entry_list.html
list` |
| `/bitacora/<uuid:pk>/` | `detail` |
| `/bitacora/create/` | `create` |
| `/bitacora/<uuid:pk>/update/` | `update` |
| `/bitacora/<uuid:pk>/delete/` | `delete` |
| `/bitacora/content-blocks/` | `content_blocks` |
| `/bitacora/<uuid:entry_id>/insert-block/<int:block_id>/` | `insert_content_block` |
| `/bitacora/upload-image/` | `upload_image` |

### `board` — namespace: `board`

| Pattern | Name |
|---------|------|
| `/board/create/` | `create` |
| `/board/<int:pk>/` | `detail` |
| `/board/htmx/<int:board_id>/grid/` | `grid` |
| `/board/htmx/<int:board_id>/create-card/` | `create_card_htmx` |
| `/board/htmx/card/<int:card_id>/delete/` | `delete_card_htmx` |
| `/board/htmx/card/<int:card_id>/toggle-pin/` | `toggle_pin` |
| `/board/htmx/<int:board_id>/load-more/` | `load_more` |

### `bots` — namespace: `bots`

| Pattern | Name |
|---------|------|
| `/bots/dashboard/` | `bot_dashboard` |
| `/bots/api/status/` | `api_bot_status` |
| `/bots/campaigns/` | `campaign_list` |
| `/bots/campaigns/create/` | `campaign_create` |
| `/bots/campaigns/<int:pk>/` | `campaign_detail` |
| `/bots/campaigns/<int:campaign_pk>/upload/` | `lead_upload` |
| `/bots/campaigns/<int:campaign_pk>/rules/` | `distribution_rules` |
| `/bots/campaigns/<int:campaign_pk>/distribute/` | `trigger_distribution` |
| `/bots/leads/` | `lead_list` |
| `/bots/leads/<int:pk>/` | `lead_detail` |
| `/bots/leads/export/` | `lead_export` |
| `/bots/api/campaigns/<int:campaign_pk>/stats/` | `api_campaign_stats` |
| `/bots/api/campaigns/<int:campaign_pk>/distribute/` | `api_trigger_distribution` |

### `campaigns` — namespace: `campaigns`

| Pattern | Name |
|---------|------|
| `/campaigns/campaigns/` | `campaign_list` |
| `/campaigns/campaigns/<uuid:pk>/` | `campaign_detail` |
| `/campaigns/campaigns/<uuid:campaign_id>/contacts/` | `contact_list` |
| `/campaigns/discador/` | `discador_loads` |
| `/campaigns/discador/<int:pk>/` | `discador_load_detail` |

### `chat` — namespace: `chat`

| Pattern | Name |
|---------|------|
| `/chat/rooms/` | `room_list` |
| `/chat/room/` | `redirect_to_last_room` |
| `/chat/room/<str:room_name>/` | `room` |
| `/chat/assistant/` | `chat_api` |
| `/chat/ui/` | `assistant_ui` |
| `/chat/functions/` | `functions_panel` |
| `/chat/commands/` | `command_history` |
| `/chat/conversations/` | `conversation_history` |
| `/chat/conversation/<str:conversation_id>/` | `conversation_detail` |
| `/chat/clear/` | `clear_history` |
| `/chat/clear_history/<str:room_name>/` | `clear_history_room` |
| `/chat/api/chat/last-room/` | `api_last_room` |
| `/chat/api/chat/room-list/` | `api_room_list` |
| `/chat/api/chat/room-history/<int:room_id>/` | `api_room_history` |
| `/chat/api/chat/mark-read/` | `api_mark_read` |
| `/chat/api/chat/unread-count/` | `api_unread_count` |
| `/chat/api/chat/reset-unread/` | `api_reset_unread` |
| `/chat/api/notifications/unread/` | `api_unread_notifications` |
| `/chat/api/notifications/mark-read/` | `api_mark_notifications_read` |
| `/chat/api/notifications/test-create/` | `api_test_create_notification` |
| `/chat/api/chat/search/` | `api_search_history` |
| `/chat/api/chat/search-messages/` | `api_search_messages` |
| `/chat/api/chat/reaction/<int:message_id>/` | `api_add_reaction` |
| `/chat/api/chat/presence/` | `api_update_presence` |
| `/chat/api/chat/presence/status/` | `api_get_presence` |
| `/chat/api/room/<int:room_id>/members/` | `api_room_members` |
| `/chat/api/room/<int:room_id>/notifications/` | `api_room_notifications` |
| `/chat/panel/` | `chat_panel` |
| `/chat/stats/` | `chat_stats` |
| `/chat/room/<int:room_id>/admin/` | `room_admin` |
| `/chat/api/conversations/` | `api_conversations` |
| `/chat/api/conversation/<str:conversation_id>/switch/` | `api_switch_conversation` |
| `/chat/api/conversation/<str:conversation_id>/messages/` | `api_conversation_messages` |
| `/chat/api/conversation/new/` | `api_new_conversation` |
| `/chat/configurations/` | `assistant_configurations` |
| `/chat/configurations/create/` | `create_assistant_configuration` |
| `/chat/configurations/<int:config_id>/edit/` | `edit_assistant_configuration` |
| `/chat/configurations/<int:config_id>/delete/` | `delete_assistant_configuration` |
| `/chat/configurations/<int:config_id>/set-active/` | `set_active_configuration` |

### `core` — namespace: `core`

| Pattern | Name |
|---------|------|
| `/core/about/` | `about` |
| `/core/contact/` | `contact` |
| `/core/faq/` | `faq` |
| `/core/gtd-guide/` | `gtd_guide` |
| `/core/blank/` | `blank` |
| `/core/<int:days>/` | `home_by_days` |
| `/core/<int:days>/<int:days_ago>/` | `home_by_days_range` |
| `/core/search/` | `search` |
| `/core/url-map/` | `url_map` |
| `/core/api/activities/more/` | `load_more_activities` |
| `/core/api/items/<str:item_type>/more/` | `load_more_recent_items` |
| `/core/api/categories/<str:category_type>/more/` | `load_more_categories` |
| `/core/api/dashboard/refresh/` | `refresh_dashboard_data` |
| `/core/api/dashboard/stats/` | `dashboard_stats` |

### `courses` — namespace: `courses`

| Pattern | Name |
|---------|------|
| `/courses/category/<slug:category_slug>/` | `course_list_by_category` |
| `/courses/dashboard/` | `dashboard` |
| `/courses/courses/` | `courses_list` |
| `/courses/<int:course_id>/enroll/` | `enroll` |
| `/courses/manage/` | `manage_courses` |
| `/courses/manage/create/` | `create_course` |
| `/courses/manage/create/wizard/` | `create_course_wizard` |
| `/courses/manage/<slug:slug>/edit/` | `edit_course` |
| `/courses/manage/<slug:slug>/delete/` | `delete_course` |
| `/courses/manage/<slug:slug>/analytics/` | `course_analytics` |
| `/courses/manage/<slug:slug>/content/` | `manage_content` |
| `/courses/manage/<slug:slug>/modules/create/` | `create_module` |
| `/courses/manage/<slug:slug>/modules/<int:module_id>/edit/` | `edit_module` |
| `/courses/manage/<slug:slug>/modules/<int:module_id>/delete/` | `delete_module` |
| `/courses/manage/<slug:slug>/modules/<int:module_id>/duplicate/` | `duplicate_module` |
| `/courses/manage/<slug:slug>/modules/<int:module_id>/statistics/` | `module_statistics` |
| `/courses/manage/<slug:slug>/modules/<int:module_id>/progress/` | `module_progress` |
| `/courses/manage/<slug:slug>/modules/bulk-actions/` | `bulk_module_actions` |
| `/courses/manage/<slug:slug>/modules/reorder/` | `reorder_modules` |
| `/courses/modules/overview/` | `modules_overview` |
| `/courses/manage/<slug:slug>/modules/<int:module_id>/lessons/create/` | `create_lesson` |
| `/courses/manage/<slug:slug>/modules/<int:module_id>/lessons/<int:lesson_id>/edit/` | `edit_lesson` |
| `/courses/manage/<slug:course_slug>/modules/<int:module_id>/lessons/<int:lesson_id>/preview/` | `preview_lesson` |
| `/courses/manage/<slug:slug>/modules/<int:module_id>/lessons/<int:lesson_id>/delete/` | `delete_lesson` |
| `/courses/manage/categories/` | `manage_categories` |
| `/courses/manage/categories/create/` | `create_category` |
| `/courses/manage/categories/quick-create/` | `quick_create_category` |
| `/courses/manage/categories/<int:category_id>/edit/` | `edit_category` |
| `/courses/manage/categories/<int:category_id>/delete/` | `delete_category` |
| `/courses/admin/` | `admin_dashboard` |
| `/courses/admin/users/` | `admin_users` |
| `/courses/admin/users/<int:user_id>/` | `admin_user_detail` |
| `/courses/admin/users/<int:user_id>/edit/` | `edit_user` |
| `/courses/content/` | `content_manager` |
| `/courses/content/create/<str:block_type>/` | `create_content_block` |
| `/courses/content/create/` | `create_content_block_default` |
| `/courses/content/<slug:slug>/edit/` | `edit_content_block` |
| `/courses/content/<slug:slug>/delete/` | `delete_content_block` |
| `/courses/content/<slug:slug>/duplicate/` | `duplicate_content_block` |
| `/courses/content/<slug:slug>/preview/` | `preview_content_block` |
| `/courses/content/my-blocks/` | `my_content_blocks` |
| `/courses/content/public/` | `public_content_blocks` |
| `/courses/content/featured/` | `featured_content_blocks` |
| `/courses/content/<slug:slug>/toggle-featured/` | `toggle_block_featured` |
| `/courses/content/<slug:slug>/toggle-public/` | `toggle_block_public` |
| `/courses/content/` | `standalone_lessons_list` |
| `/courses/lessons/my-lessons/` | `my_standalone_lessons` |
| `/courses/lessons/create/` | `create_standalone_lesson` |
| `/courses/lessons/<slug:slug>/` | `standalone_lesson_detail` |
| `/courses/lessons/<slug:slug>/edit/` | `edit_standalone_lesson` |
| `/courses/lessons/<slug:slug>/delete/` | `delete_standalone_lesson` |
| `/courses/lessons/<slug:slug>/toggle-published/` | `toggle_lesson_published` |
| `/courses/<slug:slug>/` | `course_detail` |
| `/courses/<slug:slug>/learn/` | `course_learning` |
| `/courses/<slug:slug>/learn/<int:lesson_id>/` | `course_learning_lesson` |
| `/courses/lesson/<int:lesson_id>/complete/` | `mark_lesson_complete` |
| `/courses/<int:course_id>/review/` | `add_review` |
| `/courses/docs/` | `docs` |

### `cv` — namespace: `cv`

| Pattern | Name |
|---------|------|
| `/cv/crear/` | `cv_create` |
| `/cv/editar/` | `cv_edit` |
| `/cv/ver/<int:user_id>/` | `view_cv` |
| `/cv/editar/personal/` | `edit_personal` |
| `/cv/editar/experiencia/` | `edit_experience` |
| `/cv/editar/educacion/` | `edit_education` |
| `/cv/editar/habilidades/` | `edit_skills` |
| `/cv/documentos/` | `docsview` |
| `/cv/documentos/subir/documento/` | `document_upload` |
| `/cv/documentos/subir/imagen/` | `image_upload` |
| `/cv/documentos/subir/base-datos/` | `upload_db` |
| `/cv/documentos/eliminar/<str:file_type>/<int:file_id>/` | `delete_file` |
| `/cv/view/<int:user_id>/tradicional/` | `traditional_profile` |

### `events` — namespace: `events`

| Pattern | Name |
|---------|------|
| `/events/setup/` | `setup` |
| `/events/credits/` | `add_credits` |
| `/events/root/` | `root` |
| `/events/dashboard/` | `unified_dashboard` |
| `/events/panel/` | `panel` |
| `/events/management/` | `management_index` |
| `/events/events/` | `events` |
| `/events/events/create/` | `event_create` |
| `/events/events/<int:event_id>/` | `event_detail` |
| `/events/events/edit/` | `event_edit` |
| `/events/events/<int:event_id>/edit/` | `event_edit` |
| `/events/events/<int:event_id>/delete/` | `event_delete` |
| `/events/events/<int:event_id>/status/` | `event_status_change` |
| `/events/events/<int:event_id>/assign/` | `event_assign` |
| `/events/events/<int:event_id>/history/` | `event_history` |
| `/events/events/panel/` | `event_panel` |
| `/events/events/panel/<int:event_id>/` | `event_panel_with_id` |
| `/events/events/export/` | `event_export` |
| `/events/events/bulk-action/` | `event_bulk_action` |
| `/events/events/edit/` | `event_edit_no_id` |
| `/events/events/<int:event_id>/assign-attendee/<int:user_id>/` | `assign_attendee_to_event` |
| `/events/projects/` | `projects` |
| `/events/projects/create/` | `project_create` |
| `/events/projects/<int:project_id>/` | `projects_with_id` |
| `/events/projects/<int:project_id>/detail/` | `project_detail` |
| `/events/projects/<int:project_id>/edit/` | `project_edit` |
| `/events/projects/<int:project_id>/delete/` | `project_delete` |
| `/events/projects/<int:project_id>/activate/` | `project_activate` |
| `/events/projects/<int:project_id>/status/` | `change_project_status` |
| `/events/projects/panel/` | `project_panel` |
| `/events/projects/panel/<int:project_id>/` | `project_panel_with_id` |
| `/events/projects/export/` | `project_export` |
| `/events/projects/bulk-action/` | `project_bulk_action` |
| `/events/projects/alerts/ajax/` | `project_alerts_ajax` |
| `/events/tasks/` | `tasks` |
| `/events/tasks/create/` | `task_create` |
| `/events/tasks/<int:task_id>/` | `tasks_with_id` |
| `/events/tasks/<int:task_id>/edit/` | `task_edit` |
| `/events/tasks/<int:task_id>/delete/` | `task_delete` |
| `/events/tasks/<int:task_id>/activate/` | `task_activate` |
| `/events/tasks/<int:task_id>/status/` | `change_task_status` |
| `/events/tasks/<int:task_id>/dependencies/` | `task_dependencies` |
| `/events/tasks/panel/` | `task_panel` |
| `/events/tasks/panel/<int:task_id>/` | `task_panel_with_id` |
| `/events/tasks/export/` | `task_export` |
| `/events/tasks/bulk-action/` | `task_bulk_action` |
| `/events/tasks/status/ajax/` | `task_change_status_ajax` |
| `/events/tasks/schedules/` | `task_schedules` |
| `/events/tasks/schedules/create/` | `create_task_schedule` |
| `/events/tasks/schedules/<int:schedule_id>/` | `task_schedule_detail` |
| `/events/tasks/schedules/<int:pk>/edit/` | `edit_task_schedule` |
| `/events/tasks/schedules/<int:schedule_id>/edit/enhanced/` | `edit_task_schedule_enhanced` |
| `/events/tasks/schedules/<int:schedule_id>/preview/` | `task_schedule_preview` |
| `/events/tasks/schedules/<int:schedule_id>/delete/` | `delete_task_schedule` |
| `/events/tasks/schedules/<int:schedule_id>/generate/` | `generate_schedule_occurrences` |
| `/events/tasks/schedules/admin/` | `schedule_admin_dashboard` |
| `/events/tasks/schedules/admin/bulk-action/` | `schedule_admin_bulk_action` |
| `/events/schedules/users/` | `user_schedules_panel` |
| `/events/planning/` | `planning_task` |
| `/events/task_programs_calendar/` | `task_programs_calendar` |
| `/events/inbox/` | `inbox` |
| `/events/inbox/process/` | `process_inbox_item_mailbox` |
| `/events/inbox/process/<int:item_id>/` | `process_inbox_item` |
| `/events/inbox/api/tasks/` | `inbox_api_tasks` |
| `/events/inbox/api/projects/` | `inbox_api_projects` |
| `/events/inbox/api/stats/` | `inbox_api_stats` |
| `/events/inbox/api/creation-options/` | `inbox_api_creation_options` |
| `/events/inbox/api/create-from-inbox/` | `inbox_api_create_from_inbox` |
| `/events/inbox/api/assign-item/` | `inbox_api_assign_item` |
| `/events/event/inbox/` | `event_inbox_panel` |
| `/events/panel/inbox/` | `panel_inbox` |
| `/events/inbox/admin/` | `inbox_admin_dashboard` |
| `/events/inbox/admin/<int:item_id>/` | `inbox_item_detail_admin` |
| `/events/inbox/admin/<int:item_id>/classify/` | `classify_inbox_item_admin` |
| `/events/inbox/admin/<int:item_id>/authorize/` | `authorize_inbox_item` |
| `/events/inbox/admin/bulk-action/` | `inbox_admin_bulk_action` |
| `/events/root/bulk-actions/` | `root_bulk_actions` |
| `/events/root/activate-bot/` | `activate_bot` |
| `/events/inbox/management/` | `inbox_management_panel` |
| `/events/inbox/create/` | `create_inbox_item_api` |
| `/events/inbox/management/api/queue-data/` | `get_queue_data` |
| `/events/inbox/management/api/email-queue/` | `get_email_queue_items` |
| `/events/inbox/management/api/call-queue/` | `get_call_queue_items` |
| `/events/inbox/management/api/chat-queue/` | `get_chat_queue_items` |
| `/events/inbox/management/api/process-queue/` | `process_queue` |
| `/events/inbox/management/api/update-settings/` | `update_processing_settings` |
| `/events/inbox/management/api/assign-agent/` | `assign_interaction_to_agent` |
| `/events/inbox/management/api/mark-resolved/` | `mark_interaction_resolved` |
| `/events/api/check-new-emails/` | `check_new_emails_api` |
| `/events/api/process-cx-emails/` | `process_cx_emails_api` |
| `/events/inbox/links/check/` | `inbox_link_checker` |
| `/events/inbox/api/classification-history/<int:item_id>/` | `get_classification_history` |
| `/events/inbox/classify/<int:item_id>/` | `classify_inbox_item_ajax` |
| `/events/inbox/api/consensus/<int:item_id>/` | `get_consensus_api` |
| `/events/inbox/ai/summary/` | `inbox_ai_summary` |
| `/events/inbox/ai/chat/` | `inbox_ai_chat` |
| `/events/kanban/` | `kanban_board` |
| `/events/kanban/organized/` | `kanban_board_organized` |
| `/events/kanban/project/<int:project_id>/` | `kanban_project` |
| `/events/eisenhower/` | `eisenhower_matrix` |
| `/events/eisenhower/move/<int:task_id>/<str:quadrant>/` | `move_task_eisenhower` |
| `/events/dependencies/` | `task_dependencies_list` |
| `/events/dependencies/create/<int:task_id>/` | `create_task_dependency` |
| `/events/dependencies/<int:dependency_id>/delete/` | `delete_task_dependency` |
| `/events/dependencies/graph/<int:task_id>/` | `task_dependency_graph` |
| `/events/templates/` | `project_templates` |
| `/events/templates/create/` | `create_project_template` |
| `/events/templates/<int:template_id>/` | `project_template_detail` |
| `/events/templates/<int:template_id>/edit/` | `edit_project_template` |
| `/events/templates/<int:template_id>/delete/` | `delete_project_template` |
| `/events/templates/<int:template_id>/use/` | `use_project_template` |
| `/events/reminders/` | `reminders_dashboard` |
| `/events/reminders/create/` | `create_reminder` |
| `/events/reminders/<int:reminder_id>/edit/` | `edit_reminder` |
| `/events/reminders/<int:reminder_id>/delete/` | `delete_reminder` |
| `/events/reminders/<int:reminder_id>/mark-sent/` | `mark_reminder_sent` |
| `/events/reminders/bulk-action/` | `bulk_reminder_action` |
| `/events/configuration/` | `—` |
| `/events/status/` | `status` |
| `/events/status/create/` | `status_create` |
| `/events/status/create/<int:model_id>/` | `status_create_with_model` |
| `/events/status/edit/` | `status_edit` |
| `/events/status/edit/<int:model_id>/` | `status_edit_with_model` |
| `/events/status/edit/<int:model_id>/<int:status_id>/` | `status_edit_with_id` |
| `/events/status/delete/<int:model_id>/` | `status_delete_model` |
| `/events/status/delete/<int:model_id>/<int:status_id>/` | `status_delete` |
| `/events/classifications/` | `classification_list` |
| `/events/classifications/create/` | `create_classification` |
| `/events/classifications/<int:classification_id>/edit/` | `edit_classification` |
| `/events/classifications/<int:classification_id>/delete/` | `delete_classification` |
| `/events/test-board/` | `test_board` |
| `/events/test-board/<int:id>/` | `test_board_with_id` |
| `/events/unified_dashboard/` | `unified_dashboard_alt` |
| `/events/management/events/` | `management_events` |
| `/events/management/projects/` | `management_projects` |
| `/events/management/tasks/` | `management_tasks` |
| `/events/events/assign/` | `event_assign_no_id` |
| `/events/events/history/` | `event_history_no_id` |
| `/events/projects/activate/` | `project_activate_no_id` |
| `/events/projects/edit/` | `project_edit_no_id` |
| `/events/tasks/activate/` | `task_activate_no_id` |
| `/events/tasks/edit/` | `task_edit_no_id` |
| `/events/tasks/create/<int:project_id>/` | `task_create_with_project` |
| `/events/tasks/<int:project_id>/` | `tasks_with_project_id` |
| `/events/configuration/status/create/` | `status_create_no_model` |
| `/events/configuration/status/edit/` | `status_edit_no_model` |
| `/events/configuration/status/delete/<int:model_id>/` | `status_delete_no_status_id` |

### `help` — namespace: `help`

| Pattern | Name |
|---------|------|
| `/help/categories/` | `category_list` |
| `/help/categories/<slug:slug>/` | `category_detail` |
| `/help/articles/<slug:slug>/` | `article_detail` |
| `/help/faq/` | `faq_list` |
| `/help/videos/` | `video_tutorials` |
| `/help/quick-start/` | `quick_start` |
| `/help/search/` | `search` |
| `/help/articles/<slug:article_slug>/feedback/` | `submit_feedback` |
| `/help/articles/<slug:article_slug>/feedback-stats/` | `article_feedback_stats` |

### `kpis` — namespace: `kpis`

| Pattern | Name |
|---------|------|
| `/kpis/dashboard/` | `dashboard` |
| `/kpis/api/` | `api` |
| `/kpis/export/` | `export_data` |
| `/kpis/generate-data/` | `generate_data` |

### `memento` — namespace: `memento`

| Pattern | Name |
|---------|------|
| `/memento/try/` | `memento_try` |
| `/memento/config/create/` | `memento_create` |
| `/memento/config/update/<int:pk>/` | `memento_update` |
| `/memento/view/<str:frequency>/<str:birth_date>/<str:death_date>/` | `memento` |
| `/memento/logout/` | `memento_logout` |

### `panel` — namespace: `panel`

| Pattern | Name |
|---------|------|
| `/panel/ckeditor5/upload/` | `ck_editor_5_upload_file` |
| `/panel/admin/` | `—` |
| `/panel/accounts/` | `—` |
| `/panel/campaigns/` | `—` |
| `/panel/chat/` | `—` |
| `/panel/courses/` | `—` |
| `/panel/cv/` | `—` |
| `/panel/events/` | `—` |
| `/panel/kpis/` | `—` |
| `/panel/memento/` | `—` |
| `/panel/passgen/` | `—` |
| `/panel/rooms/` | `—` |
| `/panel/bots/` | `—` |
| `/panel/help/` | `—` |
| `/panel/bitacora/` | `—` |
| `/panel/board/` | `—` |
| `/panel/analyst/` | `—` |
| `/panel/sim/` | `—` |
| `/panel/simcity/` | `—` |
| `/panel/api/csrf/` | `api-csrf` |
| `/panel/api/login/` | `api-login` |
| `/panel/api/logout/` | `api-logout` |
| `/panel/api/signup/` | `api-signup` |
| `/panel/api/token/connection/` | `api-connection-token` |
| `/panel/api/token/subscription/` | `api-subscription-token` |
| `/panel/api/` | `—` |
| `/panel/redis-test/` | `redis_test` |

### `passgen` — namespace: `passgen`

| Pattern | Name |
|---------|------|
| `/passgen/generate/` | `generate_password` |
| `/passgen/help/` | `password_help` |

### `rooms` — namespace: `rooms`

| Pattern | Name |
|---------|------|
| `/rooms/register-presence/` | `register_presence` |
| `/rooms/search/` | `room_search` |
| `/rooms/rooms/` | `room_list` |
| `/rooms/rooms/crud/` | `room_crud` |
| `/rooms/rooms/create/` | `room_create` |
| `/rooms/rooms/create-complete/` | `room_create_complete` |
| `/rooms/rooms/<int:pk>/` | `room_detail` |
| `/rooms/rooms/<int:pk>/delete/` | `room_delete` |
| `/rooms/rooms/<int:pk>/3d/` | `room_3d` |
| `/rooms/rooms/<int:pk>/3d-interactive/` | `room_3d_interactive` |
| `/rooms/rooms/<int:pk>/comments/` | `room_comments` |
| `/rooms/rooms/<int:pk>/evaluations/` | `room_evaluations` |
| `/rooms/portals/` | `portal_list` |
| `/rooms/portals/create/` | `portal_create` |
| `/rooms/portals/<int:pk>/` | `portal_detail` |
| `/rooms/entrance-exits/` | `entrance_exit_list` |
| `/rooms/entrance-exits/create/` | `entrance_exit_create` |
| `/rooms/entrance-exits/<int:pk>/` | `entrance_exit_detail` |
| `/rooms/entrance-exits/<int:pk>/edit/` | `edit_entrance_exit` |
| `/rooms/entrance-exits/<int:pk>/delete/` | `delete_entrance_exit` |
| `/rooms/rooms/<int:room_id>/connections/create/` | `create_room_connection` |
| `/rooms/rooms/<int:room_id>/connections/<int:connection_id>/edit/` | `edit_room_connection` |
| `/rooms/rooms/<int:room_id>/connections/<int:connection_id>/delete/` | `delete_room_connection` |
| `/rooms/api/rooms/` | `room-list-api` |
| `/rooms/api/rooms/<int:pk>/` | `room-detail-api` |
| `/rooms/api/rooms/search/` | `room-search-api` |
| `/rooms/api/crud/rooms/` | `—` |
| `/rooms/api/crud/rooms/<int:pk>/` | `—` |
| `/rooms/api/crud/doors/` | `—` |
| `/rooms/api/crud/doors/<int:pk>/` | `—` |
| `/rooms/api/crud/portals/` | `—` |
| `/rooms/api/crud/portals/<int:pk>/` | `—` |
| `/rooms/api/crud/connections/` | `—` |
| `/rooms/api/crud/connections/<int:pk>/` | `—` |
| `/rooms/api/rooms/<int:room_id>/messages/` | `room-messages-api` |
| `/rooms/api/rooms/<int:room_id>/join/` | `join-room-api` |
| `/rooms/api/rooms/<int:room_id>/leave/` | `leave-room-api` |
| `/rooms/api/transitions/available/` | `available-transitions-api` |
| `/rooms/api/entrance/<int:entrance_id>/use/` | `use-entrance-api` |
| `/rooms/api/entrance/<int:entrance_id>/info/` | `entrance-info-api` |
| `/rooms/api/teleport/<int:room_id>/` | `teleport-to-room-api` |
| `/rooms/api/navigation/history/` | `navigation-history-api` |
| `/rooms/api/user/current-room/` | `user-current-room-api` |
| `/rooms/api/3d/rooms/<int:room_id>/data/` | `room-3d-data-api` |
| `/rooms/api/3d/transition/` | `room-transition-api` |
| `/rooms/api/3d/player/position/` | `update-player-position-api` |
| `/rooms/api/3d/player/status/` | `player-status-api` |
| `/rooms/3d-basic/` | `basic_3d_environment` |
| `/rooms/navigation-test-zone/` | `create_navigation_test_zone` |
| `/rooms/room/` | `current_room` |
| `/rooms/room/<int:room_id>/` | `room_view` |
| `/rooms/navigate/<str:direction>/` | `navigate_room` |

### `sim` — namespace: `sim`

| Pattern | Name |
|---------|------|
| `/sim/api/` | `simulator_api` |
| `/sim/gtr/` | `gtr_panel` |
| `/sim/gtr/start/` | `gtr_start` |
| `/sim/gtr/<str:session_id>/tick/` | `gtr_tick` |
| `/sim/gtr/<str:session_id>/state/` | `gtr_state` |
| `/sim/gtr/<str:session_id>/pause/` | `gtr_pause` |
| `/sim/gtr/<str:session_id>/resume/` | `gtr_resume` |
| `/sim/gtr/<str:session_id>/event/` | `gtr_event` |
| `/sim/gtr/<str:session_id>/stop/` | `gtr_stop` |
| `/sim/gtr/<str:session_id>/interactions/` | `gtr_interactions` |
| `/sim/accounts/create/` | `account_create` |
| `/sim/accounts/<uuid:account_id>/delete/` | `account_delete` |
| `/sim/accounts/<uuid:account_id>/generate/` | `account_generate` |
| `/sim/accounts/<uuid:account_id>/clear/` | `account_clear` |
| `/sim/accounts/<uuid:account_id>/runs/` | `account_runs` |
| `/sim/accounts/<uuid:account_id>/kpis/` | `account_kpis` |
| `/sim/accounts/<uuid:account_id>/export/` | `export_interactions` |
| `/sim/accounts/<uuid:account_id>/edit/` | `account_edit` |
| `/sim/accounts/<uuid:account_id>/config/` | `account_config_save` |
| `/sim/dashboard/` | `sim_dashboard` |
| `/sim/dashboard/api/` | `dashboard_api` |
| `/sim/training/` | `training_panel` |
| `/sim/training/scenarios/api/` | `scenario_list_api` |
| `/sim/training/scenarios/create/` | `scenario_create` |
| `/sim/training/scenarios/<uuid:scenario_id>/update/` | `scenario_update` |
| `/sim/training/scenarios/<uuid:scenario_id>/delete/` | `scenario_delete` |
| `/sim/training/scenarios/<uuid:scenario_id>/start/` | `session_start` |
| `/sim/training/sessions/api/` | `session_list_api` |
| `/sim/training/sessions/<uuid:session_id>/complete/` | `session_complete` |
| `/sim/training/sessions/<uuid:session_id>/action/` | `session_log_action` |
| `/sim/training/sessions/<uuid:session_id>/notes/` | `session_trainer_notes` |
| `/sim/acd/` | `acd_panel` |
| `/sim/acd/sessions/api/` | `acd_sessions_api` |
| `/sim/acd/sessions/create/` | `acd_session_create` |
| `/sim/acd/sessions/<uuid:session_id>/state/` | `acd_session_state` |
| `/sim/acd/sessions/<uuid:session_id>/start/` | `acd_session_start` |
| `/sim/acd/sessions/<uuid:session_id>/pause/` | `acd_session_pause` |
| `/sim/acd/sessions/<uuid:session_id>/resume/` | `acd_session_resume` |
| `/sim/acd/sessions/<uuid:session_id>/stop/` | `acd_session_stop` |
| `/sim/acd/sessions/<uuid:session_id>/slots/add/` | `acd_slot_add` |
| `/sim/acd/sessions/<uuid:session_id>/slots/<uuid:slot_id>/remove/` | `acd_slot_remove` |
| `/sim/acd/sessions/<uuid:session_id>/slots/<uuid:slot_id>/control/` | `acd_slot_control` |
| `/sim/acd/sessions/<uuid:session_id>/interactions/` | `acd_interactions` |
| `/sim/acd/agent/<uuid:slot_id>/` | `acd_agent_panel` |
| `/sim/acd/agent/<uuid:slot_id>/poll/` | `acd_agent_poll` |
| `/sim/acd/agent/<uuid:slot_id>/action/` | `acd_agent_action` |
| `/sim/docs/<str:doc_key>/` | `docs_view` |

### `simcity` — namespace: `simcity`

| Pattern | Name |
|---------|------|
| `/simcity/api/games/` | `list_games` |
| `/simcity/api/games/new/` | `new_game` |
| `/simcity/api/game/<int:game_id>/map/` | `game_map` |
| `/simcity/api/game/<int:game_id>/tick/` | `tick` |
| `/simcity/api/game/<int:game_id>/build/` | `build` |
| `/simcity/api/game/<int:game_id>/reset/` | `reset` |
| `/simcity/api/game/<int:game_id>/generate_block/` | `generate_block` |
| `/simcity/api/game/<int:game_id>/generate_zr_block/` | `generate_zr_block` |
| `/simcity/api/game/<int:game_id>/census/` | `census` |
| `/simcity/api/game/<int:game_id>/tasks/` | `task_status` |
| `/simcity/api/game/<int:game_id>/delete/` | `delete_game` |
| `/simcity/api/game/<int:game_id>/export_analyst/` | `export_to_analyst` |
| `/simcity/api/game/<int:game_id>/add_money/` | `add_money` |

---

## Modelos por app

### `accounts`

- L4: `class User(AbstractUser):`

### `analyst`

- L12: `class StoredDataset(models.Model):`
- L50: `class Report(models.Model):`
- L104: `class ETLSource(models.Model):`
- L172: `class ETLJob(models.Model):`
- L212: `class AnalystBase(models.Model):`
- L315: `class CrossSource(models.Model):`
- L418: `class Dashboard(models.Model):`
- L452: `class DashboardWidget(models.Model):`
- L513: `class Pipeline(models.Model):`
- L581: `class PipelineRun(models.Model):`

### `bitacora`

- L11: `class CategoriaChoices(models.TextChoices):`
- L22: `class MoodChoices(models.TextChoices):`
- L30: `class BitacoraEntry(models.Model):`
- L99: `class BitacoraAttachment(models.Model):`

### `board`

- L8: `class Board(models.Model):`
- L43: `class Card(models.Model):`
- L88: `class Activity(models.Model):`

### `bots`

- L13: `class GenericUser(models.Model):`
- L32: `class BotCoordinator(models.Model):`
- L88: `class BotInstance(models.Model):`
- L208: `class BotTaskAssignment(models.Model):`
- L277: `class ResourceLock(models.Model):`
- L345: `class BotCommunication(models.Model):`
- L392: `class BotLog(models.Model):`
- L444: `class LeadCampaign(models.Model):`
- L483: `class Lead(models.Model):`
- L638: `class LeadDistributionRule(models.Model):`

### `campaigns`

- L6: `class ProviderRawData(models.Model):`
- L24: `class ContactRecord(models.Model):`
- L52: `class DiscadorLoad(models.Model):`

### `chat`

- L12: `class Conversation(models.Model):`
- L92: `class CommandLog(models.Model):`
- L113: `class AssistantConfiguration(models.Model):`
- L186: `class HardcodedNotificationManager:`
- L299: `class UserPresence(models.Model):`
- L331: `class MessageReaction(models.Model):`

### `core`

- L5: `class Article(models.Model):`

### `courses`

- L14: `class CourseLevelChoices(models.TextChoices):`
- L19: `class EnrollmentStatusChoices(models.TextChoices):`
- L24: `class LessonTypeChoices(models.TextChoices):`
- L33: `class CourseCategory(models.Model):`
- L49: `class Course(models.Model):`
- L125: `class Module(models.Model):`
- L141: `class LessonAttachment(models.Model):`
- L235: `class Lesson(models.Model):`
- L329: `class Enrollment(models.Model):`
- L353: `class Progress(models.Model):`
- L383: `class Review(models.Model):`
- L420: `class ContentBlock(models.Model):`

### `cv`

- L21: `class RoleChoices(models.TextChoices):`
- L30: `class Curriculum(models.Model):`
- L100: `class Experience(models.Model):`
- L128: `class Education(models.Model):`
- L157: `class Skill(models.Model):`
- L183: `class Language(models.Model):`
- L210: `class Certification(models.Model):`
- L241: `class Document(models.Model):`
- L257: `class Image(models.Model):`
- L273: `class Database(models.Model):`

### `events`

- L12: `class Status(models.Model):`
- L21: `class ProjectStatus(models.Model):`
- L30: `class TaskStatus(models.Model):`
- L40: `class Classification(models.Model):`
- L48: `class ProjectState(models.Model):`
- L67: `class ProjectHistory(models.Model):`
- L79: `class Project(models.Model):`
- L139: `class ProjectAttendee(models.Model):`
- L147: `class TaskState(models.Model):`
- L166: `class TaskHistory(models.Model):`
- L178: `class Task(models.Model):`
- L255: `class TaskProgram(models.Model):`
- L276: `class TaskSchedule(models.Model):`
- L445: `class EventState(models.Model):`
- L464: `class EventHistory(models.Model):`
- L476: `class TagCategory(models.Model):`
- L489: `class Tag(models.Model):`
- L504: `class Event(models.Model):`
- L559: `class EventAttendee(models.Model):`
- L568: `class CreditAccount(models.Model):`
- L591: `class TaskDependency(models.Model):`
- L609: `class ProjectTemplate(models.Model):`
- L621: `class TemplateTask(models.Model):`
- L636: `class InboxItem(models.Model):`
- L836: `class Reminder(models.Model):`
- L859: `class InboxItemAuthorization(models.Model):`
- L878: `class InboxItemClassification(models.Model):`
- L917: `class InboxItemHistory(models.Model):`
- L942: `class GTDClassificationPattern(models.Model):`
- L1002: `class GTDLearningEntry(models.Model):`
- L1031: `class GTDProcessingSettings(models.Model):`

### `help`

- L9: `class HelpCategory(models.Model):`
- L37: `class HelpArticle(models.Model):`
- L214: `class FAQ(models.Model):`
- L241: `class HelpSearchLog(models.Model):`
- L264: `class HelpFeedback(models.Model):`
- L295: `class VideoTutorial(models.Model):`
- L376: `class QuickStartGuide(models.Model):`

### `kpis`

- L37: `class CallRecord(models.Model):`
- L115: `class ExchangeRate(models.Model):`

### `rooms`

- L8: `class PlayerProfile(models.Model):`
- L215: `class RoomManager(models.Manager):`
- L218: `class Room(models.Model):`
- L388: `class RoomConnection(models.Model):`
- L401: `class RoomObject(models.Model):`
- L430: `class EntranceExit(models.Model):`
- L668: `class Portal(models.Model):`
- L684: `class Comment(models.Model):`
- L691: `class Evaluation(models.Model):`
- L699: `class RoomMember(models.Model):`
- L727: `class Message(models.Model):`
- L758: `class MessageRead(models.Model):`
- L766: `class Notification(models.Model):`
- L804: `class RoomNotification(models.Model):`
- L832: `class Outbox(models.Model):`
- L839: `class CDC(models.Model):`

### `sim`

- L41: `class SimAccount(models.Model):`
- L99: `class SimAgent(models.Model):`
- L127: `class Interaction(models.Model):`
- L179: `class SimRun(models.Model):`
- L215: `class TrainingScenario(models.Model):`
- L279: `class TrainingSession(models.Model):`
- L332: `class SimAgentProfile(models.Model):`
- L477: `class ACDSession(models.Model):`
- L531: `class ACDAgentSlot(models.Model):`
- L605: `class ACDInteraction(models.Model):`
- L666: `class ACDAgentAction(models.Model):`

### `simcity`

- L4: `class Game(models.Model):`

---

## Integración con url-map del sistema

La vista `/url-map/` en el servidor usa `core/utils.py::get_all_apps_url_structure()`
que parsea todos los `urls.py` del proyecto. Este archivo es su equivalente estático.

```
GET /url-map/                      → vista HTML de todas las apps
GET /url-map/?app_name=analyst     → detalle de una app
```

---

## Comandos útiles

```bash
# Análisis profundo de una app específica:
bash scripts/m360_map.sh app ./analyst
bash scripts/m360_map.sh app ./sim

# Auditoría de residuos en nav:
bash scripts/m360_map.sh app ./analyst --audit

# Mapa de URLs en consola:
bash scripts/m360_map.sh urls

# Regenerar este archivo:
bash scripts/m360_map.sh
```
