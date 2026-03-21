# Mapa de Contexto — App `events`

> Generado por `m360_map.sh`  |  2026-03-20 17:13:29
> Ruta: `/data/data/com.termux/files/home/projects/Management360/events`  |  Total archivos: **243**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 22 |
| 2 | 🎨 `templates` | 152 |
| 3 | 🗃 `models` | 1 |
| 4 | 📝 `forms` | 1 |
| 5 | ⚙️ `services` | 3 |
| 6 | 🔧 `utils` | 13 |
| 7 | 🔗 `urls` | 1 |
| 8 | 🛡 `admin` | 1 |
| 9 | 📄 `management` | 13 |
| 10 | 🧪 `tests` | 12 |
| 11 | 📄 `other` | 24 |

---

## Archivos por Categoría


### VIEWS (22 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `old_views.py` | 514 | `_old_scripts/old_views.py` |
| `views.py` | 253 | `_old_scripts/views.py` |
| `views_bkup.py` | 3847 | `_old_scripts/views_bkup.py` |
| `gtd_reviews.py` | 756 | `gtd_reviews.py` |
| `setup_views.py` | 337 | `setup_views.py` |
| `__init__.py` | 19 | `views/__init__.py` |
| `ai_assistant.py` | 420 | `views/ai_assistant.py` |
| `bot_views.py` | 368 | `views/bot_views.py` |
| `classification_views.py` | 50 | `views/classification_views.py` |
| `credits_views.py` | 46 | `views/credits_views.py` |
| `dashboard_views.py` | 552 | `views/dashboard_views.py` |
| `dependencies_views.py` | 341 | `views/dependencies_views.py` |
| `eisenhower_views.py` | 165 | `views/eisenhower_views.py` |
| `events_views.py` | 1003 | `views/events_views.py` |
| `gtd_views.py` | 2702 | `views/gtd_views.py` |
| `kanban_views.py` | 230 | `views/kanban_views.py` |
| `projects_views.py` | 1167 | `views/projects_views.py` |
| `reminders_views.py` | 228 | `views/reminders_views.py` |
| `schedules_views.py` | 875 | `views/schedules_views.py` |
| `status_views.py` | 217 | `views/status_views.py` |
| `tasks_views.py` | 1193 | `views/tasks_views.py` |
| `templates_views.py` | 320 | `views/templates_views.py` |

### TEMPLATES (152 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `classification_list.html` | 28 | `templates/configuration/classification_list.html` |
| `confirm_delete.html` | 22 | `templates/configuration/confirm_delete.html` |
| `create_classification.html` | 18 | `templates/configuration/create_classification.html` |
| `create_status.html` | 18 | `templates/configuration/create_status.html` |
| `edit_classification.html` | 20 | `templates/configuration/edit_classification.html` |
| `status.html` | 30 | `templates/configuration/status.html` |
| `status_create.html` | 58 | `templates/configuration/status_create.html` |
| `status_edit.html` | 58 | `templates/configuration/status_edit.html` |
| `status_list.html` | 49 | `templates/configuration/status_list.html` |
| `add_credits.html` | 11 | `templates/credits/add_credits.html` |
| `docsview.html` | 805 | `templates/documents/docsview.html` |
| `upload.html` | 23 | `templates/documents/upload.html` |
| `upload_xlsx.html` | 23 | `templates/documents/upload_xlsx.html` |
| `inbox_floating_button.css` | 301 | `templates/events/components/inbox_floating_button.css` |
| `inbox_floating_button.html` | 441 | `templates/events/components/inbox_floating_button.html` |
| `inbox_floating_button.js` | 558 | `templates/events/components/inbox_floating_button.js` |
| `control.html` | 25 | `templates/events/control/control.html` |
| `frame.html` | 30 | `templates/events/control/frame.html` |
| `create_project_template.html` | 316 | `templates/events/create_project_template.html` |
| `create_reminder.html` | 151 | `templates/events/create_reminder.html` |
| `create_task_dependency.html` | 237 | `templates/events/create_task_dependency.html` |
| `create_task_schedule.html` | 686 | `templates/events/create_task_schedule.html` |
| `delete_project_template.html` | 184 | `templates/events/delete_project_template.html` |
| `delete_reminder.html` | 83 | `templates/events/delete_reminder.html` |
| `delete_task_dependency.html` | 145 | `templates/events/delete_task_dependency.html` |
| `delete_task_schedule.html` | 92 | `templates/events/delete_task_schedule.html` |
| `edit_project_template.html` | 322 | `templates/events/edit_project_template.html` |
| `edit_reminder.html` | 151 | `templates/events/edit_reminder.html` |
| `edit_task_schedule.html` | 666 | `templates/events/edit_task_schedule.html` |
| `edit_task_schedule_enhanced.html` | 1708 | `templates/events/edit_task_schedule_enhanced.html` |
| `eisenhower_matrix.html` | 570 | `templates/events/eisenhower_matrix.html` |
| `event_assign.html` | 171 | `templates/events/event_assign.html` |
| `event_card2.html` | 71 | `templates/events/event_card2.html` |
| `event_create.html` | 233 | `templates/events/event_create.html` |
| `event_detail.html` | 397 | `templates/events/event_detail.html` |
| `event_edit.html` | 164 | `templates/events/event_edit.html` |
| `event_history.html` | 97 | `templates/events/event_history.html` |
| `event_list.html` | 922 | `templates/events/event_list.html` |
| `event_panel.html` | 325 | `templates/events/event_panel.html` |
| `events.html` | 139 | `templates/events/events.html` |
| `generate_schedule_occurrences.html` | 139 | `templates/events/generate_schedule_occurrences.html` |
| `inbox.html` | 483 | `templates/events/inbox.html` |
| `inbox_admin_dashboard.html` | 503 | `templates/events/inbox_admin_dashboard.html` |
| `inbox_item_detail_admin.html` | 528 | `templates/events/inbox_item_detail_admin.html` |
| `inbox_link_checker.html` | 154 | `templates/events/inbox_link_checker.html` |
| `inbox_mailbox.html` | 545 | `templates/events/inbox_mailbox.html` |
| `inbox_management_panel.html` | 1068 | `templates/events/inbox_management_panel.html` |
| `inbox_panel.html` | 348 | `templates/events/inbox_panel.html` |
| `activity_card.html` | 69 | `templates/events/includes/activity_card.html` |
| `event_card.html` | 106 | `templates/events/includes/event_card.html` |
| `event_form.html` | 59 | `templates/events/includes/event_form.html` |
| `filter_card.html` | 71 | `templates/events/includes/filter_card.html` |
| `form_card.html` | 36 | `templates/events/includes/form_card.html` |
| `inbox_item_card.html` | 27 | `templates/events/includes/inbox_item_card.html` |
| `messages.html` | 36 | `templates/events/includes/messages.html` |
| `metrics_cards.html` | 83 | `templates/events/includes/metrics_cards.html` |
| `processed_item_card.html` | 30 | `templates/events/includes/processed_item_card.html` |
| `top_table.html` | 182 | `templates/events/includes/top_table.html` |
| `kanban.html` | 1563 | `templates/events/kanban.html` |
| `kanban_board.html` | 745 | `templates/events/kanban_board.html` |
| `kanban_board_modern.html` | 2170 | `templates/events/kanban_board_modern.html` |
| `kanban_enhanced.html` | 1006 | `templates/events/kanban_enhanced.html` |
| `message_container.html` | 7 | `templates/events/message_container.html` |
| `process_inbox_item.html` | 586 | `templates/events/process_inbox_item.html` |
| `project_template_detail.html` | 288 | `templates/events/project_template_detail.html` |
| `project_templates.html` | 247 | `templates/events/project_templates.html` |
| `reminders_dashboard.html` | 217 | `templates/events/reminders_dashboard.html` |
| `root.html` | 1515 | `templates/events/root.html` |
| `schedule_admin_dashboard.html` | 284 | `templates/events/schedule_admin_dashboard.html` |
| `task_dependencies.html` | 290 | `templates/events/task_dependencies.html` |
| `task_dependencies_list.html` | 286 | `templates/events/task_dependencies_list.html` |
| `task_dependency_graph.html` | 370 | `templates/events/task_dependency_graph.html` |
| `task_programs_calendar.html` | 185 | `templates/events/task_programs_calendar.html` |
| `task_schedule_detail.html` | 193 | `templates/events/task_schedule_detail.html` |
| `task_schedule_preview.html` | 400 | `templates/events/task_schedule_preview.html` |
| `task_schedules.html` | 465 | `templates/events/task_schedules.html` |
| `unified_dashboard.html` | 342 | `templates/events/unified_dashboard.html` |
| `use_project_template.html` | 292 | `templates/events/use_project_template.html` |
| `user_schedules_panel.html` | 319 | `templates/events/user_schedules_panel.html` |
| `card.html` | 11 | `templates/index/includes/card.html` |
| `dashboard_sales_card.html` | 147 | `templates/index/includes/dashboard_sales_card.html` |
| `news.html` | 50 | `templates/index/includes/news.html` |
| `revenue_card.html` | 31 | `templates/index/includes/revenue_card.html` |
| `slide.html` | 52 | `templates/index/includes/slide.html` |
| `top.html` | 72 | `templates/index/includes/top.html` |
| `index copy.html` | 676 | `templates/index/index copy.html` |
| `old_index.html` | 36 | `templates/index/old_index.html` |
| `index.html` | 232 | `templates/management/index.html` |
| `memento_dayly.html` | 72 | `templates/memento/includes/memento_dayly.html` |
| `memento_weekly.html` | 56 | `templates/memento/includes/memento_weekly.html` |
| `memento_mori.html` | 77 | `templates/memento/memento_mori.html` |
| `panel.html` | 187 | `templates/panel/panel.html` |
| `program.html` | 200 | `templates/program/program.html` |
| `confirm_force_close.html` | 10 | `templates/projects/confirm_force_close.html` |
| `control.html` | 26 | `templates/projects/control/control.html` |
| `frame.html` | 26 | `templates/projects/control/frame.html` |
| `acordeon.html` | 27 | `templates/projects/includes/acordeon.html` |
| `other_links.html` | 6 | `templates/projects/includes/other_links.html` |
| `project_card.html` | 207 | `templates/projects/includes/project_card.html` |
| `project_links_card.html` | 12 | `templates/projects/includes/project_links_card.html` |
| `project_recent_activity.html` | 38 | `templates/projects/includes/project_recent_activity.html` |
| `project_recent_sales.html` | 61 | `templates/projects/includes/project_recent_sales.html` |
| `project_revenue.html` | 37 | `templates/projects/includes/project_revenue.html` |
| `project_table_optimized.html` | 167 | `templates/projects/includes/project_table_optimized.html` |
| `project_tasks.html` | 223 | `templates/projects/includes/project_tasks.html` |
| `project_top.html` | 449 | `templates/projects/includes/project_top.html` |
| `project_total_card.html` | 36 | `templates/projects/includes/project_total_card.html` |
| `project_activate.html` | 49 | `templates/projects/project_activate.html` |
| `project_create.html` | 79 | `templates/projects/project_create.html` |
| `project_detail.html` | 991 | `templates/projects/project_detail.html` |
| `project_edit.html` | 80 | `templates/projects/project_edit.html` |
| `project_list.html` | 122 | `templates/projects/project_list.html` |
| `project_panel.html` | 1187 | `templates/projects/project_panel.html` |
| `projects.html` | 739 | `templates/projects/projects.html` |
| `projects_check.html` | 56 | `templates/projects/projects_check.html` |
| `setup.html` | 2060 | `templates/setup/setup.html` |
| `control.html` | 25 | `templates/tasks/control/control.html` |
| `frame.html` | 30 | `templates/tasks/control/frame.html` |
| `messages_display.html` | 13 | `templates/tasks/includes/messages_display.html` |
| `task_acordeon.html` | 27 | `templates/tasks/includes/task_acordeon.html` |
| `task_alerts.html` | 20 | `templates/tasks/includes/task_alerts.html` |
| `task_card.html` | 299 | `templates/tasks/includes/task_card.html` |
| `task_card_compact.html` | 0 | `templates/tasks/includes/task_card_compact.html` |
| `task_cards_view.html` | 84 | `templates/tasks/includes/task_cards_view.html` |
| `task_empty_state.html` | 15 | `templates/tasks/includes/task_empty_state.html` |
| `task_filters.html` | 76 | `templates/tasks/includes/task_filters.html` |
| `task_kanban_board.html` | 151 | `templates/tasks/includes/task_kanban_board.html` |
| `task_kanban_card.html` | 208 | `templates/tasks/includes/task_kanban_card.html` |
| `task_links.html` | 6 | `templates/tasks/includes/task_links.html` |
| `task_links_card.html` | 12 | `templates/tasks/includes/task_links_card.html` |
| `task_quick_actions.html` | 57 | `templates/tasks/includes/task_quick_actions.html` |
| `task_recent.html` | 56 | `templates/tasks/includes/task_recent.html` |
| `task_recent_activity.html` | 61 | `templates/tasks/includes/task_recent_activity.html` |
| `task_sidebar_stats.html` | 48 | `templates/tasks/includes/task_sidebar_stats.html` |
| `task_stats_cards.html` | 127 | `templates/tasks/includes/task_stats_cards.html` |
| `task_table_optimized.html` | 344 | `templates/tasks/includes/task_table_optimized.html` |
| `task_top_.html` | 328 | `templates/tasks/includes/task_top_.html` |
| `task_total.html` | 36 | `templates/tasks/includes/task_total.html` |
| `task_view_selector.html` | 55 | `templates/tasks/includes/task_view_selector.html` |
| `task_activate.html` | 49 | `templates/tasks/task_activate.html` |
| `task_create.html` | 186 | `templates/tasks/task_create.html` |
| `task_detail.html` | 340 | `templates/tasks/task_detail.html` |
| `task_edit.html` | 190 | `templates/tasks/task_edit.html` |
| `task_list.html` | 101 | `templates/tasks/task_list.html` |
| `task_panel.html` | 230 | `templates/tasks/task_panel.html` |
| `tasks.html` | 165 | `templates/tasks/tasks.html` |
| `chart_bar.html` | 37 | `templates/tests/chart_bar.html` |
| `chart_report.html` | 93 | `templates/tests/chart_report.html` |
| `chart_time.html` | 51 | `templates/tests/chart_time.html` |
| `chart_trend.html` | 66 | `templates/tests/chart_trend.html` |
| `table.html` | 75 | `templates/tests/table.html` |
| `test.html` | 53 | `templates/tests/test.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 1083 | `models.py` |

### FORMS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `forms.py` | 528 | `forms.py` |

### SERVICES (3 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 9 | `services/__init__.py` |
| `bot_simulation.py` | 258 | `services/bot_simulation.py` |
| `dashboard_service.py` | 387 | `services/dashboard_service.py` |

### UTILS (13 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 187 | `utils/__init__.py` |
| `chart_utils.py` | 352 | `utils/chart_utils.py` |
| `credit_utils.py` | 119 | `utils/credit_utils.py` |
| `dashboard_utils.py` | 186 | `utils/dashboard_utils.py` |
| `gtd_utils.py` | 341 | `utils/gtd_utils.py` |
| `managers.py` | 54 | `utils/managers.py` |
| `metric_utils.py` | 210 | `utils/metric_utils.py` |
| `permission_utils.py` | 158 | `utils/permission_utils.py` |
| `profile_utils.py` | 124 | `utils/profile_utils.py` |
| `project_utils.py` | 232 | `utils/project_utils.py` |
| `schedule_utils.py` | 34 | `utils/schedule_utils.py` |
| `status_utils.py` | 149 | `utils/status_utils.py` |
| `time_utils.py` | 182 | `utils/time_utils.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 225 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 2062 | `admin.py` |

### MANAGEMENT (13 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `management/__init__.py` |
| `__init__.py` | 0 | `management/commands/__init__.py` |
| `ensure_statuses.py` | 48 | `management/commands/ensure_statuses.py` |
| `process_cx_emails.py` | 327 | `management/commands/process_cx_emails.py` |
| `schedule_cx_email_processing.py` | 77 | `management/commands/schedule_cx_email_processing.py` |
| `set_admin_role.py` | 63 | `management/commands/set_admin_role.py` |
| `setup_advanced_tags.py` | 144 | `management/commands/setup_advanced_tags.py` |
| `update_chart_cache.py` | 131 | `management/commands/update_chart_cache.py` |
| `create_credit_accounts.py` | 17 | `management/create_credit_accounts.py` |
| `event_manager.py` | 91 | `management/event_manager.py` |
| `project_manager.py` | 132 | `management/project_manager.py` |
| `task_manager.py` | 211 | `management/task_manager.py` |
| `utils.py` | 262 | `management/utils.py` |

### TESTS (12 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `create_test_schedules.py` | 156 | `management/commands/create_test_schedules.py` |
| `test_click_simulation.py` | 158 | `management/commands/test_click_simulation.py` |
| `test_models.py` | 354 | `test_models.py` |
| `__init__.py` | 3 | `tests/__init__.py` |
| `test_events_views.py` | 834 | `tests/test_events_views.py` |
| `test_inbox_duplication.py` | 147 | `tests/test_inbox_duplication.py` |
| `test_inbox_task_workflow.py` | 425 | `tests/test_inbox_task_workflow.py` |
| `test_link_to_task.py` | 898 | `tests/test_link_to_task.py` |
| `test_runner.py` | 23 | `tests/test_runner.py` |
| `test_settings.py` | 147 | `tests/test_settings.py` |
| `test_task_schedule.py` | 686 | `tests/test_task_schedule.py` |
| `test_views.py` | 260 | `views/test_views.py` |

### OTHER (24 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `EVENTS_CONTEXT.md` | 1117 | `EVENTS_CONTEXT.md` |
| `EVENTS_DESIGN.md` | 133 | `EVENTS_DESIGN.md` |
| `EVENTS_DEV_REFERENCE.md` | 396 | `EVENTS_DEV_REFERENCE.md` |
| `EVENTS_HANDOFF_SPRINT8.md` | 121 | `EVENTS_HANDOFF_SPRINT8.md` |
| `GTD_README.md` | 144 | `GTD_README.md` |
| `README_ROOT_REFACTOR.md` | 190 | `README_ROOT_REFACTOR.md` |
| `__init__.py` | 0 | `__init__.py` |
| `fix_imports.sh` | 73 | `_old_scripts/fix_imports.sh` |
| `move_views_to_package.sh` | 128 | `_old_scripts/move_views_to_package.sh` |
| `apps.py` | 16 | `apps.py` |
| `gtd_analytics.py` | 937 | `gtd_analytics.py` |
| `gtd_calendar.py` | 719 | `gtd_calendar.py` |
| `gtd_config.py` | 536 | `gtd_config.py` |
| `gtd_metrics.py` | 902 | `gtd_metrics.py` |
| `gtd_utils.py` | 470 | `gtd_utils.py` |
| `initial_data.py` | 132 | `initial_data.py` |
| `my_utils.py` | 61 | `my_utils.py` |
| `signals.py` | 81 | `signals.py` |
| `__init__.py` | 0 | `templatetags/__init__.py` |
| `custom_tags.py` | 16 | `templatetags/custom_tags.py` |
| `event_extras.py` | 63 | `templatetags/event_extras.py` |
| `inbox_tags.py` | 82 | `templatetags/inbox_tags.py` |
| `schedule_filters.py` | 38 | `templatetags/schedule_filters.py` |
| `signals.py` | 130 | `templatetags/signals.py` |

---

## Árbol de Directorios

```
events/
├── _old_scripts
│   ├── fix_imports.sh
│   ├── move_views_to_package.sh
│   ├── old_views.py
│   ├── views.py
│   └── views_bkup.py
├── management
│   ├── commands
│   │   ├── __init__.py
│   │   ├── create_test_schedules.py
│   │   ├── ensure_statuses.py
│   │   ├── process_cx_emails.py
│   │   ├── schedule_cx_email_processing.py
│   │   ├── set_admin_role.py
│   │   ├── setup_advanced_tags.py
│   │   ├── test_click_simulation.py
│   │   └── update_chart_cache.py
│   ├── __init__.py
│   ├── create_credit_accounts.py
│   ├── event_manager.py
│   ├── project_manager.py
│   ├── task_manager.py
│   └── utils.py
├── services
│   ├── __init__.py
│   ├── bot_simulation.py
│   └── dashboard_service.py
├── templates
│   ├── configuration
│   │   ├── classification_list.html
│   │   ├── confirm_delete.html
│   │   ├── create_classification.html
│   │   ├── create_status.html
│   │   ├── edit_classification.html
│   │   ├── status.html
│   │   ├── status_create.html
│   │   ├── status_edit.html
│   │   └── status_list.html
│   ├── credits
│   │   └── add_credits.html
│   ├── documents
│   │   ├── docsview.html
│   │   ├── upload.html
│   │   └── upload_xlsx.html
│   ├── events
│   │   ├── components
│   │   │   ├── inbox_floating_button.css
│   │   │   ├── inbox_floating_button.html
│   │   │   └── inbox_floating_button.js
│   │   ├── control
│   │   │   ├── control.html
│   │   │   └── frame.html
│   │   ├── includes
│   │   │   ├── activity_card.html
│   │   │   ├── event_card.html
│   │   │   ├── event_form.html
│   │   │   ├── filter_card.html
│   │   │   ├── form_card.html
│   │   │   ├── inbox_item_card.html
│   │   │   ├── messages.html
│   │   │   ├── metrics_cards.html
│   │   │   ├── processed_item_card.html
│   │   │   └── top_table.html
│   │   ├── create_project_template.html
│   │   ├── create_reminder.html
│   │   ├── create_task_dependency.html
│   │   ├── create_task_schedule.html
│   │   ├── delete_project_template.html
│   │   ├── delete_reminder.html
│   │   ├── delete_task_dependency.html
│   │   ├── delete_task_schedule.html
│   │   ├── edit_project_template.html
│   │   ├── edit_reminder.html
│   │   ├── edit_task_schedule.html
│   │   ├── edit_task_schedule_enhanced.html
│   │   ├── eisenhower_matrix.html
│   │   ├── event_assign.html
│   │   ├── event_card2.html
│   │   ├── event_create.html
│   │   ├── event_detail.html
│   │   ├── event_edit.html
│   │   ├── event_history.html
│   │   ├── event_list.html
│   │   ├── event_panel.html
│   │   ├── events.html
│   │   ├── generate_schedule_occurrences.html
│   │   ├── inbox.html
│   │   ├── inbox_admin_dashboard.html
│   │   ├── inbox_item_detail_admin.html
│   │   ├── inbox_link_checker.html
│   │   ├── inbox_mailbox.html
│   │   ├── inbox_management_panel.html
│   │   ├── inbox_panel.html
│   │   ├── kanban.html
│   │   ├── kanban_board.html
│   │   ├── kanban_board_modern.html
│   │   ├── kanban_enhanced.html
│   │   ├── message_container.html
│   │   ├── process_inbox_item.html
│   │   ├── project_template_detail.html
│   │   ├── project_templates.html
│   │   ├── reminders_dashboard.html
│   │   ├── root.html
│   │   ├── schedule_admin_dashboard.html
│   │   ├── task_dependencies.html
│   │   ├── task_dependencies_list.html
│   │   ├── task_dependency_graph.html
│   │   ├── task_programs_calendar.html
│   │   ├── task_schedule_detail.html
│   │   ├── task_schedule_preview.html
│   │   ├── task_schedules.html
│   │   ├── unified_dashboard.html
│   │   ├── use_project_template.html
│   │   └── user_schedules_panel.html
│   ├── index
│   │   ├── includes
│   │   │   ├── card.html
│   │   │   ├── dashboard_sales_card.html
│   │   │   ├── news.html
│   │   │   ├── revenue_card.html
│   │   │   ├── slide.html
│   │   │   └── top.html
│   │   ├── index copy.html
│   │   └── old_index.html
│   ├── management
│   │   └── index.html
│   ├── memento
│   │   ├── includes
│   │   │   ├── memento_dayly.html
│   │   │   └── memento_weekly.html
│   │   └── memento_mori.html
│   ├── panel
│   │   └── panel.html
│   ├── program
│   │   └── program.html
│   ├── projects
│   │   ├── control
│   │   │   ├── control.html
│   │   │   └── frame.html
│   │   ├── includes
│   │   │   ├── acordeon.html
│   │   │   ├── other_links.html
│   │   │   ├── project_card.html
│   │   │   ├── project_links_card.html
│   │   │   ├── project_recent_activity.html
│   │   │   ├── project_recent_sales.html
│   │   │   ├── project_revenue.html
│   │   │   ├── project_table_optimized.html
│   │   │   ├── project_tasks.html
│   │   │   ├── project_top.html
│   │   │   └── project_total_card.html
│   │   ├── confirm_force_close.html
│   │   ├── project_activate.html
│   │   ├── project_create.html
│   │   ├── project_detail.html
│   │   ├── project_edit.html
│   │   ├── project_list.html
│   │   ├── project_panel.html
│   │   ├── projects.html
│   │   └── projects_check.html
│   ├── setup
│   │   └── setup.html
│   ├── tasks
│   │   ├── control
│   │   │   ├── control.html
│   │   │   └── frame.html
│   │   ├── includes
│   │   │   ├── messages_display.html
│   │   │   ├── task_acordeon.html
│   │   │   ├── task_alerts.html
│   │   │   ├── task_card.html
│   │   │   ├── task_card_compact.html
│   │   │   ├── task_cards_view.html
│   │   │   ├── task_empty_state.html
│   │   │   ├── task_filters.html
│   │   │   ├── task_kanban_board.html
│   │   │   ├── task_kanban_card.html
│   │   │   ├── task_links.html
│   │   │   ├── task_links_card.html
│   │   │   ├── task_quick_actions.html
│   │   │   ├── task_recent.html
│   │   │   ├── task_recent_activity.html
│   │   │   ├── task_sidebar_stats.html
│   │   │   ├── task_stats_cards.html
│   │   │   ├── task_table_optimized.html
│   │   │   ├── task_top_.html
│   │   │   ├── task_total.html
│   │   │   └── task_view_selector.html
│   │   ├── task_activate.html
│   │   ├── task_create.html
│   │   ├── task_detail.html
│   │   ├── task_edit.html
│   │   ├── task_list.html
│   │   ├── task_panel.html
│   │   └── tasks.html
│   └── tests
│       ├── chart_bar.html
│       ├── chart_report.html
│       ├── chart_time.html
│       ├── chart_trend.html
│       ├── table.html
│       └── test.html
├── templatetags
│   ├── __init__.py
│   ├── custom_tags.py
│   ├── event_extras.py
│   ├── inbox_tags.py
│   ├── schedule_filters.py
│   └── signals.py
├── tests
│   ├── __init__.py
│   ├── test_events_views.py
│   ├── test_inbox_duplication.py
│   ├── test_inbox_task_workflow.py
│   ├── test_link_to_task.py
│   ├── test_runner.py
│   ├── test_settings.py
│   └── test_task_schedule.py
├── utils
│   ├── __init__.py
│   ├── chart_utils.py
│   ├── credit_utils.py
│   ├── dashboard_utils.py
│   ├── gtd_utils.py
│   ├── managers.py
│   ├── metric_utils.py
│   ├── permission_utils.py
│   ├── profile_utils.py
│   ├── project_utils.py
│   ├── schedule_utils.py
│   ├── status_utils.py
│   └── time_utils.py
├── views
│   ├── __init__.py
│   ├── ai_assistant.py
│   ├── bot_views.py
│   ├── classification_views.py
│   ├── credits_views.py
│   ├── dashboard_views.py
│   ├── dependencies_views.py
│   ├── eisenhower_views.py
│   ├── events_views.py
│   ├── gtd_views.py
│   ├── kanban_views.py
│   ├── projects_views.py
│   ├── reminders_views.py
│   ├── schedules_views.py
│   ├── status_views.py
│   ├── tasks_views.py
│   ├── templates_views.py
│   └── test_views.py
├── EVENTS_CONTEXT.md
├── EVENTS_DESIGN.md
├── EVENTS_DEV_REFERENCE.md
├── EVENTS_HANDOFF_SPRINT8.md
├── GTD_README.md
├── README_ROOT_REFACTOR.md
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── gtd_analytics.py
├── gtd_calendar.py
├── gtd_config.py
├── gtd_metrics.py
├── gtd_reviews.py
├── gtd_utils.py
├── initial_data.py
├── models.py
├── my_utils.py
├── setup_views.py
├── signals.py
├── test_models.py
└── urls.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `events`

```python
  path('setup/', SetupView.as_view(), name='setup'),
  path('credits/', add_credits, name='add_credits'),  # Sin views.
  path('root/', root, name='root'),
  path('dashboard/', unified_dashboard, name='unified_dashboard'),
  path('panel/', panel, name='panel'),
  path('management/', management_index, name='management_index'),
  path('events/', events, name='events'),
  path('events/create/', event_create, name='event_create'),
  path('events/<int:event_id>/', event_detail, name='event_detail'),
  path('events/edit/', event_edit, name='event_edit'),
  path('events/<int:event_id>/edit/', event_edit, name='event_edit'),
  path('events/<int:event_id>/delete/', event_delete, name='event_delete'),
  path('events/<int:event_id>/status/', event_status_change, name='event_status_change'),
  path('events/<int:event_id>/assign/', event_assign, name='event_assign'),
  path('events/<int:event_id>/history/', event_history, name='event_history'),
  path('events/panel/', event_panel, name='event_panel'),
  path('events/panel/<int:event_id>/', event_panel, name='event_panel_with_id'),
  path('events/export/', event_export, name='event_export'),
  path('events/bulk-action/', event_bulk_action, name='event_bulk_action'),
  path('events/edit/', event_edit, name='event_edit_no_id'),
  path('events/<int:event_id>/assign-attendee/<int:user_id>/', assign_attendee_to_event, name='assign_attendee_to_event'),
  path('projects/', projects, name='projects'),
  path('projects/create/', project_create, name='project_create'),
  path('projects/<int:project_id>/', projects, name='projects_with_id'),
  path('projects/<int:project_id>/detail/', project_detail, name='project_detail'),
  path('projects/<int:project_id>/edit/', project_edit, name='project_edit'),
  path('projects/<int:project_id>/delete/', project_delete, name='project_delete'),
  path('projects/<int:project_id>/activate/', project_activate, name='project_activate'),
  path('projects/<int:project_id>/status/', change_project_status, name='change_project_status'),
  path('projects/panel/', project_panel, name='project_panel'),
  path('projects/panel/<int:project_id>/', project_panel, name='project_panel_with_id'),
  path('projects/export/', project_export, name='project_export'),
  path('projects/bulk-action/', project_bulk_action, name='project_bulk_action'),
  path('projects/alerts/ajax/', get_project_alerts_ajax, name='project_alerts_ajax'),
  path('tasks/', tasks, name='tasks'),
  path('tasks/create/', task_create, name='task_create'),
  path('tasks/<int:task_id>/', tasks, name='tasks_with_id'),
  path('tasks/<int:task_id>/edit/', task_edit, name='task_edit'),
  path('tasks/<int:task_id>/delete/', task_delete, name='task_delete'),
  path('tasks/<int:task_id>/activate/', task_activate, name='task_activate'),
  path('tasks/<int:task_id>/status/', change_task_status, name='change_task_status'),
  path('tasks/<int:task_id>/dependencies/', task_dependencies, name='task_dependencies'),
  path('tasks/panel/', task_panel, name='task_panel'),
  path('tasks/panel/<int:task_id>/', task_panel, name='task_panel_with_id'),
  path('tasks/export/', task_export, name='task_export'),
  path('tasks/bulk-action/', task_bulk_action, name='task_bulk_action'),
  path('tasks/status/ajax/', task_change_status_ajax, name='task_change_status_ajax'),
  path('tasks/schedules/', task_schedules, name='task_schedules'),
  path('tasks/schedules/create/', create_task_schedule, name='create_task_schedule'),
  path('tasks/schedules/<int:schedule_id>/', task_schedule_detail, name='task_schedule_detail'),
  path('tasks/schedules/<int:pk>/edit/', TaskScheduleEditView.as_view(), name='edit_task_schedule'),
  path('tasks/schedules/<int:schedule_id>/edit/enhanced/', edit_task_schedule, name='edit_task_schedule_enhanced'),
  path('tasks/schedules/<int:schedule_id>/preview/', task_schedule_preview, name='task_schedule_preview'),
  path('tasks/schedules/<int:schedule_id>/delete/', delete_task_schedule, name='delete_task_schedule'),
  path('tasks/schedules/<int:schedule_id>/generate/', generate_schedule_occurrences, name='generate_schedule_occurrences'),
  path('tasks/schedules/admin/', schedule_admin_dashboard, name='schedule_admin_dashboard'),
  path('tasks/schedules/admin/bulk-action/', schedule_admin_bulk_action, name='schedule_admin_bulk_action'),
  path('schedules/users/', user_schedules_panel, name='user_schedules_panel'),
  path('planning/', planning_task, name='planning_task'),
  path('task_programs_calendar/', task_programs_calendar, name='task_programs_calendar'),
  path('inbox/', inbox_view, name='inbox'),
  path('inbox/process/', process_inbox_item, name='process_inbox_item_mailbox'),
  path('inbox/process/<int:item_id>/', process_inbox_item, name='process_inbox_item'),
  path('inbox/api/tasks/', get_available_tasks, name='inbox_api_tasks'),
  path('inbox/api/projects/', get_available_projects, name='inbox_api_projects'),
  path('inbox/api/stats/', inbox_stats_api, name='inbox_api_stats'),
  path('inbox/api/creation-options/', get_inbox_creation_options, name='inbox_api_creation_options'),
  path('inbox/api/create-from-inbox/', create_from_inbox_api, name='inbox_api_create_from_inbox'),
  path('inbox/api/assign-item/', assign_inbox_item_api, name='inbox_api_assign_item'),
  path('event/inbox/', event_inbox_panel, name='event_inbox_panel'),
  path('panel/inbox/', event_inbox_panel, name='panel_inbox'),
  path('inbox/admin/', inbox_admin_dashboard, name='inbox_admin_dashboard'),
  path('inbox/admin/<int:item_id>/', inbox_item_detail_admin, name='inbox_item_detail_admin'),
  path('inbox/admin/<int:item_id>/classify/', classify_inbox_item_admin, name='classify_inbox_item_admin'),
  path('inbox/admin/<int:item_id>/authorize/', authorize_inbox_item, name='authorize_inbox_item'),
  path('inbox/admin/bulk-action/', inbox_admin_bulk_action, name='inbox_admin_bulk_action'),
  path('root/bulk-actions/', root_bulk_actions, name='root_bulk_actions'),
  path('root/activate-bot/', activate_bot, name='activate_bot'),
  path('inbox/management/', inbox_management_panel, name='inbox_management_panel'),
  path('inbox/create/', create_inbox_item_api, name='create_inbox_item_api'),
  path('inbox/management/api/queue-data/', get_queue_data, name='get_queue_data'),
  path('inbox/management/api/email-queue/', get_email_queue_items, name='get_email_queue_items'),
  path('inbox/management/api/call-queue/', get_call_queue_items, name='get_call_queue_items'),
  path('inbox/management/api/chat-queue/', get_chat_queue_items, name='get_chat_queue_items'),
  path('inbox/management/api/process-queue/', process_queue, name='process_queue'),
  path('inbox/management/api/update-settings/', update_processing_settings, name='update_processing_settings'),
  path('inbox/management/api/assign-agent/', assign_interaction_to_agent, name='assign_interaction_to_agent'),
  path('inbox/management/api/mark-resolved/', mark_interaction_resolved, name='mark_interaction_resolved'),
  path('api/check-new-emails/', check_new_emails_api, name='check_new_emails_api'),
  path('api/process-cx-emails/', process_cx_emails_api, name='process_cx_emails_api'),
  path('inbox/links/check/', inbox_link_checker, name='inbox_link_checker'),
  path('inbox/api/classification-history/<int:item_id>/', get_classification_history, name='get_classification_history'),
  path('inbox/classify/<int:item_id>/', classify_inbox_item_ajax, name='classify_inbox_item_ajax'),
  path('inbox/api/consensus/<int:item_id>/', get_consensus_api, name='get_consensus_api'),
  path('inbox/ai/summary/', inbox_ai_summary, name='inbox_ai_summary'),
  path('inbox/ai/chat/',    inbox_ai_chat,    name='inbox_ai_chat'),
  path('kanban/', kanban_board_unified, name='kanban_board'),
  path('kanban/organized/', kanban_board_unified, name='kanban_board_organized'),
  path('kanban/project/<int:project_id>/', kanban_project, name='kanban_project'),
  path('eisenhower/', eisenhower_matrix, name='eisenhower_matrix'),
  path('eisenhower/move/<int:task_id>/<str:quadrant>/', move_task_eisenhower, name='move_task_eisenhower'),
  path('dependencies/', task_dependencies, name='task_dependencies_list'),
  path('dependencies/create/<int:task_id>/', create_task_dependency, name='create_task_dependency'),
  path('dependencies/<int:dependency_id>/delete/', delete_task_dependency, name='delete_task_dependency'),
  path('dependencies/graph/<int:task_id>/', task_dependency_graph, name='task_dependency_graph'),
  path('templates/', project_templates, name='project_templates'),
  path('templates/create/', create_project_template, name='create_project_template'),
  path('templates/<int:template_id>/', project_template_detail, name='project_template_detail'),
  path('templates/<int:template_id>/edit/', edit_project_template, name='edit_project_template'),
  path('templates/<int:template_id>/delete/', delete_project_template, name='delete_project_template'),
  path('templates/<int:template_id>/use/', use_project_template, name='use_project_template'),
  path('reminders/', reminders_dashboard, name='reminders_dashboard'),
  path('reminders/create/', create_reminder, name='create_reminder'),
  path('reminders/<int:reminder_id>/edit/', edit_reminder, name='edit_reminder'),
  path('reminders/<int:reminder_id>/delete/', delete_reminder, name='delete_reminder'),
  path('reminders/<int:reminder_id>/mark-sent/', mark_reminder_sent, name='mark_reminder_sent'),
  path('reminders/bulk-action/', bulk_reminder_action, name='bulk_reminder_action'),
  path('configuration/', include([
  path('status/', status, name='status'),
  path('status/create/', status_create, name='status_create'),
  path('status/create/<int:model_id>/', status_create, name='status_create_with_model'),
  path('status/edit/', status_edit, name='status_edit'),
  path('status/edit/<int:model_id>/', status_edit, name='status_edit_with_model'),
  path('status/edit/<int:model_id>/<int:status_id>/', status_edit, name='status_edit_with_id'),
  path('status/delete/<int:model_id>/', status_delete, name='status_delete_model'),
  path('status/delete/<int:model_id>/<int:status_id>/', status_delete, name='status_delete'),
  path('classifications/', Classification_list, name='classification_list'),
  path('classifications/create/', create_Classification, name='create_classification'),
  path('classifications/<int:classification_id>/edit/', edit_Classification, name='edit_classification'),
  path('classifications/<int:classification_id>/delete/', delete_Classification, name='delete_classification'),
  path('test-board/', test_board, name='test_board'),
  path('test-board/<int:id>/', test_board, name='test_board_with_id'),
  path('unified_dashboard/', unified_dashboard, name='unified_dashboard_alt'),
  path('management/events/', events, name='management_events'),
  path('management/projects/', projects, name='management_projects'),
  path('management/tasks/', tasks, name='management_tasks'),
  path('events/assign/', event_assign, name='event_assign_no_id'),
  path('events/history/', event_history, name='event_history_no_id'),
  path('projects/activate/', project_activate, name='project_activate_no_id'),
  path('projects/edit/', project_edit, name='project_edit_no_id'),
  path('tasks/activate/', task_activate, name='task_activate_no_id'),
  path('tasks/edit/', task_edit, name='task_edit_no_id'),
  path('tasks/create/<int:project_id>/', task_create, name='task_create_with_project'),
  path('tasks/<int:project_id>/', tasks, name='tasks_with_project_id'),
  path('configuration/status/create/', status_create, name='status_create_no_model'),
  path('configuration/status/edit/', status_edit, name='status_edit_no_model'),
  path('configuration/status/delete/<int:model_id>/', status_delete, name='status_delete_no_status_id'),
```

---

## Modelos detectados

**`models.py`**

- línea 12: `class Status(models.Model):`
- línea 21: `class ProjectStatus(models.Model):`
- línea 30: `class TaskStatus(models.Model):`
- línea 40: `class Classification(models.Model):`
- línea 48: `class ProjectState(models.Model):`
- línea 67: `class ProjectHistory(models.Model):`
- línea 79: `class Project(models.Model):`
- línea 139: `class ProjectAttendee(models.Model):`
- línea 147: `class TaskState(models.Model):`
- línea 166: `class TaskHistory(models.Model):`
- línea 178: `class Task(models.Model):`
- línea 255: `class TaskProgram(models.Model):`
- línea 276: `class TaskSchedule(models.Model):`
- línea 445: `class EventState(models.Model):`
- línea 464: `class EventHistory(models.Model):`
- línea 476: `class TagCategory(models.Model):`
- línea 489: `class Tag(models.Model):`
- línea 504: `class Event(models.Model):`
- línea 559: `class EventAttendee(models.Model):`
- línea 568: `class CreditAccount(models.Model):`
- línea 591: `class TaskDependency(models.Model):`
- línea 609: `class ProjectTemplate(models.Model):`
- línea 621: `class TemplateTask(models.Model):`
- línea 636: `class InboxItem(models.Model):`
- línea 836: `class Reminder(models.Model):`
- línea 859: `class InboxItemAuthorization(models.Model):`
- línea 878: `class InboxItemClassification(models.Model):`
- línea 917: `class InboxItemHistory(models.Model):`
- línea 942: `class GTDClassificationPattern(models.Model):`
- línea 1002: `class GTDLearningEntry(models.Model):`
- línea 1031: `class GTDProcessingSettings(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |
| `0002_alter_gtdclassificationpattern_options_and_more` | aplicada |
| `0003_alter_gtdclassificationpattern_options_and_more` | aplicada |
| `0004_fix_fk_auth_user_to_accounts_user` | aplicada |

---

## Funciones clave (views/ y services/)

**`views/ai_assistant.py`**

```
42:def _call_ollama(prompt: str) -> str | None:
64:def _build_gtd_context(user) -> dict:
192:def _context_to_summary_text(ctx: dict) -> str:
245:def _static_analysis(ctx: dict) -> str:
309:def inbox_ai_summary(request):
360:def inbox_ai_chat(request):
```

**`views/bot_views.py`**

```
59:def check_new_emails_api(request):
106:def process_cx_emails_api(request):
157:def activate_bot(request):
210:def _user_can_activate_bots(user):
222:def _validate_bot_request(bot_id, selected_tasks):
247:def _execute_bot_tasks(bot_config, selected_tasks, user):
262:def _execute_single_task(task_function_name, user):
300:def create_project_simulation(user):
306:def manage_tasks_simulation(user):
312:def generate_reports_simulation(user):
318:def simulate_inbox_simulation(user):
324:def create_course_simulation(user):
330:def create_lesson_simulation(user):
336:def create_content_simulation(user):
342:def manage_students_simulation(user):
348:def simulate_client_inbox(user):
354:def simulate_email_sending(user):
360:def create_support_tickets(user):
366:def simulate_phone_calls(user):
```

**`views/classification_views.py`**

```
11:def create_Classification(request):
21:def edit_Classification(request, Classification_id):
39:def delete_Classification(request, Classification_id):
46:def Classification_list(request):
```

**`views/credits_views.py`**

```
18:def add_credits(request):
```

**`views/dashboard_views.py`**

```
37:def unified_dashboard(request):
171:def root(request):
253:def root_bulk_actions(request):
314:def _handle_mark_processed(request, items):
338:def _handle_mark_unprocessed(request, items):
362:def _handle_change_priority(request, items):
386:def _handle_assign_to_user(request, items):
415:def _handle_change_category(request, items):
439:def _handle_delegate(request, items):
494:def _handle_delete(items):
511:def management_index(request):
```

**`views/dependencies_views.py`**

```
22:def task_dependencies(request, task_id=None):
41:def _handle_specific_task_dependencies(request, task_id):
80:def _handle_all_dependencies(request):
100:def create_task_dependency(request, task_id):
120:def _process_create_dependency(request, task):
163:def _render_create_dependency_form(request, task):
183:def delete_task_dependency(request, dependency_id):
211:def _process_delete_dependency(request, dependency, task_id):
229:def task_dependency_graph(request, task_id):
258:def _get_all_dependencies(task, visited=None):
296:def _build_graph_structure(main_task, all_dependencies):
304:    def add_task_to_graph(task_obj):
```

**`views/eisenhower_views.py`**

```
19:def eisenhower_matrix(request):
115:def move_task_eisenhower(request, task_id, quadrant):
```

**`views/events_views.py`**

```
58:def events(request):
105:def event_detail(request, event_id):
129:def event_panel(request, event_id=None):
161:def event_create(request):
178:def event_edit(request, event_id=None):
204:def event_assign(request, event_id=None):
226:def event_status_change(request, event_id):
250:def assign_attendee_to_event(request, event_id, user_id):
283:def event_delete(request, event_id):
303:def event_bulk_action(request):
354:def event_export(request):
393:def event_history(request, event_id=None):
435:def _initialize_session_filters(request, today):
450:def _apply_filters_from_request(request, all_events):
465:def _apply_stored_filters(request, all_events):
475:def _apply_filters_to_events(events, completed, status, date_str):
506:def _count_events_updated_today(events, today):
518:def _get_event_detail_context(event):
561:def _render_event_detail_panel(request, event_id, title, managers,
612:def _render_event_general_panel(request, title, event_manager,
637:def _calculate_event_statistics(events):
662:def _prepare_event_details_dict(events):
681:def _render_event_create_form(request, title):
701:def _process_event_create_form(request, title):
745:def _assign_to_specific_event(request, event_id, title,
```

**`views/gtd_views.py`**

```
47:def find_similar_tasks(user, title, description=None, threshold=0.6):
59:    def normalize_text(text):
95:def find_similar_projects(user, title, description=None, threshold=0.6):
107:    def normalize_text(text):
147:def _create_event_for_inbox_item(inbox_item, user, context_type="inbox"):
177:def _create_project_with_event(inbox_item, user, event=None):
195:def _create_task_with_context(inbox_item, user, project=None, event=None, assigned_to=None):
231:def _link_inbox_to_object(inbox_item, user, content_object, content_type):
309:def inbox_view(request):
413:def event_inbox_panel(request):
460:def inbox_stats_api(request):
558:def process_inbox_item(request, item_id=None):
572:def _render_inbox_list(request):
590:def _process_single_inbox_item(request, item_id, logger):
615:def _handle_post_action(request, inbox_item, item_id, logger):
658:def _handle_convert_to_task(request, inbox_item, item_id, logger):
751:def _handle_convert_to_project(request, inbox_item, item_id, logger):
798:def _handle_convert_to_event(request, inbox_item, item_id, logger):
816:def _handle_convert_to_task_project(request, inbox_item, item_id, logger):
847:def _handle_link_to_task(request, inbox_item, item_id, logger):
889:def _handle_link_to_project(request, inbox_item, item_id, logger):
922:def _handle_link_to_event(request, inbox_item, item_id, logger):
955:def _handle_delete(request, inbox_item, item_id, logger):
961:def _handle_postpone(request, inbox_item, item_id, logger):
966:def _handle_categorize(request, inbox_item, item_id, logger):
```

**`views/kanban_views.py`**

```
21:def kanban_board_unified(request):
164:def kanban_project(request, project_id):
```

**`views/projects_views.py`**

```
30:def get_projects_for_user(user):
83:def render_single_project_view(request, project_id, title, statuses):
154:def render_project_panel_view(request, title, statuses):
249:def generate_project_alerts(project_data, user):
330:def generate_projects_overview_alerts(projects_data, user):
438:def generate_performance_alerts(projects_data, user):
515:def projects(request, project_id=None):
635:def project_panel(request, project_id=None):
657:def project_detail(request, project_id):
744:def project_create(request):
825:def project_edit(request, project_id=None):
898:def project_delete(request, project_id):
923:def change_project_status(request, project_id):
958:def project_activate(request, project_id=None):
1000:def project_bulk_action(request):
1040:def project_export(request):
1080:def get_project_alerts_ajax(request):
1109:def project_tasks_status_check(request, project_id):
```

**`views/reminders_views.py`**

```
26:def reminders_dashboard(request):
76:def create_reminder(request):
105:def edit_reminder(request, reminder_id):
134:def delete_reminder(request, reminder_id):
163:def mark_reminder_sent(request, reminder_id):
190:def bulk_reminder_action(request):
```

**`views/schedules_views.py`**

```
30:def planning_task(request):
129:def task_programs_calendar(request):
227:def task_schedules(request):
262:def create_task_schedule(request):
284:def task_schedule_detail(request, schedule_id):
318:def edit_task_schedule(request, schedule_id):
399:    def get_queryset(self):
403:    def get_form_class(self):
407:    def get_form_kwargs(self):
413:    def get_context_data(self, **kwargs):
446:    def form_valid(self, form):
474:    def form_invalid(self, form):
483:    def get_success_url(self):
487:    def _log_schedule_changes(self, schedule, changed_fields, original_values=None):
517:def task_schedule_preview(request, schedule_id):
586:def delete_task_schedule(request, schedule_id):
611:def generate_schedule_occurrences(request, schedule_id):
645:def user_schedules_panel(request):
742:def schedule_admin_dashboard(request):
830:def schedule_admin_bulk_action(request):
```

**`views/status_views.py`**

```
13:def status(request):
35:def status_edit(request, model_id=None, status_id=None):
119:def status_create(request, model_id=None):  
187:def status_delete(request, model_id, status_id):
```

**`views/tasks_views.py`**

```
43:def get_statuses():
54:def get_tasks_for_user(user):
141:def render_single_task_view(request, task_id, title, other_task_statuses, statuses):
237:def render_task_panel_view(request, title, other_task_statuses, statuses, tasks_states):
336:def generate_task_alerts(task_data, user):
386:def generate_tasks_overview_alerts(tasks_data, user):
475:def generate_task_performance_alerts(tasks_data, user):
524:def tasks(request, task_id=None, project_id=None):
634:def task_panel(request, task_id=None):
671:def task_create(request, project_id=None):
746:def task_edit(request, task_id=None):
798:def task_delete(request, task_id):
821:def change_task_status(request, task_id):
857:def task_activate(request, task_id=None):
947:def task_change_status_ajax(request):
1140:def task_export(request):
1169:def task_bulk_action(request):
```

**`views/templates_views.py`**

```
25:def project_templates(request):
70:def create_project_template(request):
117:def project_template_detail(request, template_id):
144:def edit_project_template(request, template_id):
202:def delete_project_template(request, template_id):
238:def use_project_template(request, template_id):
```

**`views/test_views.py`**

```
30:def test_board(request, id=None):
69:def _get_task_states_data():
104:def _format_task_states_with_duration(task_states):
128:def _get_bar_chart_data(task_states):
142:def _get_line_chart_data(task_states):
164:def _get_duration_chart_data(task_states):
185:def _get_creation_data(user):
221:def _filter_and_count_by_date(data, key_name, start_date):
233:def _count_created_per_day(data, key_name):
245:def _generate_combined_chart_data(start_date, today, projects_counts, tasks_counts, events_counts):
253:    def fill_data_for_dates(date_range, counts):
```

**`services/bot_simulation.py`**

```
8:def create_project_simulation(user):
34:def manage_tasks_simulation(user):
65:def generate_reports_simulation(user):
79:def simulate_inbox_simulation(user):
99:def create_course_simulation(user):
119:def create_lesson_simulation(user):
144:def create_content_simulation(user):
168:def manage_students_simulation(user):
188:def simulate_client_inbox(user):
214:def simulate_email_sending(user):
221:def create_support_tickets(user):
240:def simulate_phone_calls(user):
```

**`services/dashboard_service.py`**

```
52:    def from_request(cls, request) -> 'RootFilters':
73:    def _validate_choice(self, value: str, valid_choices: list) -> str:
77:    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
87:    def get_ordering(self) -> str:
94:    def apply_to_queryset(self, queryset):
152:    def get_dashboard_data(self) -> Dict[str, Any]:
185:    def _get_user_info(self) -> Dict[str, Any]:
199:    def _get_profile_info(self) -> Dict[str, Any]:
210:    def _get_user_role(self) -> str:
224:    def _get_role_badge_class(self) -> str:
236:    def _get_player_info(self) -> Dict[str, Any]:
251:    def _get_inbox_items_page(self):
274:    def _get_inbox_stats(self) -> Dict[str, int]:
301:    def _get_email_backend_info(self) -> Dict[str, Any]:
335:    def _get_all_inbox_items_page(self):
344:    def _get_users_for_filter(self):
360:    def _get_all_users_for_delegation(self):
371:    def _get_total_pages(self) -> int:
378:    def _has_active_filters(self) -> bool:
```


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/events/views/mi_vista.py | termux-clipboard-set
```
