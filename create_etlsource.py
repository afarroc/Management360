import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Create analyst_etlsource table
sql_etlsource = '''
CREATE TABLE `analyst_etlsource` (
  `id` uuid NOT NULL PRIMARY KEY,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `model_path` varchar(200) NOT NULL,
  `fields` json NOT NULL,
  `filters` json NOT NULL,
  `date_field` varchar(100) NOT NULL,
  `aggregations` json NOT NULL,
  `sql_override` longtext NOT NULL,
  `chunk_size` integer UNSIGNED NOT NULL CHECK (`chunk_size` >= 0),
  `max_rows` integer UNSIGNED NOT NULL CHECK (`max_rows` >= 0),
  `frequency` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `created_by_id` bigint NOT NULL
)
'''
try:
    cursor.execute(sql_etlsource)
    print('Table analyst_etlsource created successfully')
except Exception as e:
    print('Error creating analyst_etlsource table:', e)

# Create analyst_etljob table
sql_etljob = '''
CREATE TABLE `analyst_etljob` (
  `id` uuid NOT NULL PRIMARY KEY,
  `runtime_params` json NOT NULL,
  `status` varchar(20) NOT NULL,
  `error_msg` longtext NOT NULL,
  `rows_extracted` integer UNSIGNED NOT NULL CHECK (`rows_extracted` >= 0),
  `duration_s` double precision NOT NULL,
  `started_at` datetime(6) NULL,
  `finished_at` datetime(6) NULL,
  `created_at` datetime(6) NOT NULL,
  `result_dataset_id` uuid NULL,
  `triggered_by_id` bigint NOT NULL,
  `source_id` uuid NOT NULL
)
'''
try:
    cursor.execute(sql_etljob)
    print('Table analyst_etljob created successfully')
except Exception as e:
    print('Error creating analyst_etljob table:', e)

# Add foreign key constraints for analyst_etlsource
try:
    fk1 = '''ALTER TABLE `analyst_etlsource` 
    ADD CONSTRAINT `analyst_etlsource_created_by_id_fa8613a6_fk_accounts_user_id` 
    FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`)'''
    cursor.execute(fk1)
    print('Created_by foreign key added to analyst_etlsource')
except Exception as e:
    print('Error adding created_by foreign key to analyst_etlsource:', e)

# Add foreign key constraints for analyst_etljob
try:
    fk2 = '''ALTER TABLE `analyst_etljob` 
    ADD CONSTRAINT `analyst_etljob_result_dataset_id_f267d994_fk_analyst_s` 
    FOREIGN KEY (`result_dataset_id`) REFERENCES `analyst_storeddataset` (`id`)'''
    cursor.execute(fk2)
    print('Result_dataset foreign key added to analyst_etljob')
except Exception as e:
    print('Error adding result_dataset foreign key to analyst_etljob:', e)

try:
    fk3 = '''ALTER TABLE `analyst_etljob` 
    ADD CONSTRAINT `analyst_etljob_triggered_by_id_ed7a00ff_fk_accounts_user_id` 
    FOREIGN KEY (`triggered_by_id`) REFERENCES `accounts_user` (`id`)'''
    cursor.execute(fk3)
    print('Triggered_by foreign key added to analyst_etljob')
except Exception as e:
    print('Error adding triggered_by foreign key to analyst_etljob:', e)

try:
    fk4 = '''ALTER TABLE `analyst_etljob` 
    ADD CONSTRAINT `analyst_etljob_source_id_be08dd0a_fk_analyst_etlsource_id` 
    FOREIGN KEY (`source_id`) REFERENCES `analyst_etlsource` (`id`)'''
    cursor.execute(fk4)
    print('Source foreign key added to analyst_etljob')
except Exception as e:
    print('Error adding source foreign key to analyst_etljob:', e)

conn.close()