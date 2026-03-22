# sim/urls.py
from django.urls import path
from sim.views import simulator, gtr, dashboard, account_editor, training, docs, acd

app_name = 'sim'

urlpatterns = [
    # Panel principal
    path('',                                          simulator.simulator_list,     name='simulator_list'),
    path('api/',                                      simulator.simulator_api,      name='simulator_api'),

    # GTR
    path('gtr/',                                      gtr.gtr_panel,                name='gtr_panel'),
    path('gtr/start/',                                gtr.gtr_start,                name='gtr_start'),
    path('gtr/<str:session_id>/tick/',                gtr.gtr_tick,                 name='gtr_tick'),
    path('gtr/<str:session_id>/state/',               gtr.gtr_state,                name='gtr_state'),
    path('gtr/<str:session_id>/pause/',               gtr.gtr_pause,                name='gtr_pause'),
    path('gtr/<str:session_id>/resume/',              gtr.gtr_resume,               name='gtr_resume'),
    path('gtr/<str:session_id>/event/',               gtr.gtr_event,                name='gtr_event'),
    path('gtr/<str:session_id>/stop/',                gtr.gtr_stop,                 name='gtr_stop'),
    path('gtr/<str:session_id>/interactions/',        gtr.gtr_interactions,         name='gtr_interactions'),

    # Cuentas
    path('accounts/create/',                          simulator.account_create,     name='account_create'),
    path('accounts/<uuid:account_id>/delete/',        simulator.account_delete,     name='account_delete'),
    path('accounts/<uuid:account_id>/generate/',      simulator.account_generate,   name='account_generate'),
    path('accounts/<uuid:account_id>/clear/',         simulator.account_clear,      name='account_clear'),
    path('accounts/<uuid:account_id>/runs/',          simulator.account_runs,       name='account_runs'),
    path('accounts/<uuid:account_id>/kpis/',          simulator.account_kpis,       name='account_kpis'),
    path('accounts/<uuid:account_id>/export/',        simulator.export_interactions, name='export_interactions'),
    path('accounts/<uuid:account_id>/edit/',          account_editor.account_edit,        name='account_edit'),
    path('accounts/<uuid:account_id>/config/',        account_editor.account_config_save, name='account_config_save'),

    # Dashboard sim
    path('dashboard/',      dashboard.sim_dashboard, name='sim_dashboard'),
    path('dashboard/api/',  dashboard.dashboard_api, name='dashboard_api'),

    # SIM-5: Training Mode
    path('training/',                                      training.training_panel,        name='training_panel'),
    path('training/scenarios/api/',                        training.scenario_list_api,     name='scenario_list_api'),
    path('training/scenarios/create/',                     training.scenario_create,       name='scenario_create'),
    path('training/scenarios/<uuid:scenario_id>/update/',  training.scenario_update,       name='scenario_update'),
    path('training/scenarios/<uuid:scenario_id>/delete/',  training.scenario_delete,       name='scenario_delete'),
    path('training/scenarios/<uuid:scenario_id>/start/',   training.session_start,         name='session_start'),
    path('training/sessions/api/',                         training.session_list_api,      name='session_list_api'),
    path('training/sessions/<uuid:session_id>/complete/',  training.session_complete,      name='session_complete'),
    path('training/sessions/<uuid:session_id>/action/',    training.session_log_action,    name='session_log_action'),
    path('training/sessions/<uuid:session_id>/notes/',     training.session_trainer_notes, name='session_trainer_notes'),

    # SIM-7a: ACD Simulator
    path('acd/',                                                    acd.acd_panel,           name='acd_panel'),
    path('acd/sessions/api/',                                       acd.acd_sessions_api,    name='acd_sessions_api'),
    path('acd/sessions/create/',                                    acd.acd_session_create,  name='acd_session_create'),
    path('acd/sessions/<uuid:session_id>/state/',                   acd.acd_session_state,   name='acd_session_state'),
    path('acd/sessions/<uuid:session_id>/start/',                   acd.acd_session_start,   name='acd_session_start'),
    path('acd/sessions/<uuid:session_id>/pause/',                   acd.acd_session_pause,   name='acd_session_pause'),
    path('acd/sessions/<uuid:session_id>/resume/',                  acd.acd_session_resume,  name='acd_session_resume'),
    path('acd/sessions/<uuid:session_id>/stop/',                    acd.acd_session_stop,    name='acd_session_stop'),
    path('acd/sessions/<uuid:session_id>/slots/add/',               acd.acd_slot_add,        name='acd_slot_add'),
    path('acd/sessions/<uuid:pk>/bots/add/',                        acd.acd_add_bots,        name='acd_add_bots'),
    path('acd/sessions/<uuid:session_id>/slots/<uuid:slot_id>/remove/',  acd.acd_slot_remove,  name='acd_slot_remove'),
    path('acd/sessions/<uuid:session_id>/slots/<uuid:slot_id>/control/', acd.acd_slot_control, name='acd_slot_control'),
    path('acd/sessions/<uuid:session_id>/interactions/',            acd.acd_interactions,    name='acd_interactions'),
    path('acd/agent/<uuid:slot_id>/',                               acd.acd_agent_panel,     name='acd_agent_panel'),
    path('acd/agent/<uuid:slot_id>/poll/',                          acd.acd_agent_poll,      name='acd_agent_poll'),
    path('acd/agent/<uuid:slot_id>/action/',                        acd.acd_agent_action,    name='acd_agent_action'),

    # Documentación
    path('docs/<str:doc_key>/',                            docs.docs_view,                 name='docs_view'),
]
