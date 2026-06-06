import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Create analyst_pipeline table
sql_pipeline = '''
CREATE TABLE `analyst_pipeline` (
  `id` uuid NOT NULL PRIMARY KEY,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `steps` json NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `source_dataset_id` uuid NULL,
  `created_by_id` bigint NOT NULL
)
'''
try:
    cursor.execute(sql_pipeline)
    print('Table analyst_pipeline created successfully')
except Exception as e:
    print('Error creating analyst_pipeline table:', e)

# Create analyst_pipelinerun table
sql_pipelinerun = '''
CREATE TABLE `analyst_pipelinerun` (
  `id` uuid NOT NULL PRIMARY KEY,
  `status` varchar(20) NOT NULL,
  `error_msg` longtext NOT NULL,
  `steps_completed` integer UNSIGNED NOT NULL CHECK (`steps_completed` >= 0),
  `duration_s` double precision NOT NULL,
  `runtime_params` json NOT NULL,
  `started_at` datetime(6) NULL,
  `finished_at` datetime(6) NULL,
  `created_at` datetime(6) NOT NULL,
  `pipeline_id` uuid NOT NULL,
  `input_dataset_id` uuid NOT NULL,
  `result_dataset_id` uuid NOT NULL,
  `triggered_by_id` bigint NOT NULL
)
'''
try:
    cursor.execute(sql_pipelinerun)
    print('Table analyst_pipelinerun created successfully')
except Exception as e:
    print('Error creating analyst_pipelinerun table:', e)

# Add foreign key constraints for analyst_pipeline
try:
    fk1 = '''ALTER TABLE `analyst_pipeline` 
    ADD CONSTRAINT `analyst_pipeline_source_dataset_id_680b5e03_fk_analyst_s` 
    FOREIGN KEY (`source_dataset_id`) REFERENCES `analyst_storeddataset` (`id`)'''
    cursor.execute(fk1)
    print('Source_dataset foreign key added to analyst_pipeline')
except Exception as e:
    print('Error adding source_dataset foreign key to analyst_pipeline:', e)

try:
    fk2 = '''ALTER TABLE `analyst_pipeline` 
    ADD CONSTRAINT `analyst_pipeline_created_by_id_b40941bb_fk_accounts_user_id` 
    FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`)'''
    cursor.execute(fk2)
    print('Created_by foreign key added to analyst_pipeline')
except Exception as e:
    print('Error adding created_by foreign key to analyst_pipeline:', e)

# Add foreign key constraints for analyst_pipelinerun
try:
    fk3 = '''ALTER TABLE `analyst_pipelinerun` 
    ADD CONSTRAINT `analyst_pipelinerun_pipeline_id_c5b7bd1d_fk_analyst_pipeline_id` 
    FOREIGN KEY (`pipeline_id`) REFERENCES `analyst_pipeline` (`id`)'''
    cursor.execute(fk3)
    print('Pipeline foreign key added to analyst_pipelinerun')
except Exception as e:
    print('Error adding pipeline foreign key to analyst_pipelinerun:', e)

try:
    fk4 = '''ALTER TABLE `analyst_pipelinerun` 
    ADD CONSTRAINT `analyst_pipelinerun_input_dataset_id_988b6b0f_fk_analyst_s` 
    FOREIGN KEY (`input_dataset_id`) REFERENCES `analyst_storeddataset` (`id`)'''
    cursor.execute(fk4)
    print('Input_dataset foreign key added to analyst_pipelinerun')
except Exception as e:
    print('Error adding input_dataset foreign key to analyst_pipelinerun:', e)

try:
    fk5 = '''ALTER TABLE `analyst_pipelinerun` 
    ADD CONSTRAINT `analyst_pipelinerun_result_dataset_id_c0b64e90_fk_analyst_s` 
    FOREIGN KEY (`result_dataset_id`) REFERENCES `analyst_storeddataset` (`id`)'''
    cursor.execute(fk5)
    print('Result_dataset foreign key added to analyst_pipelinerun')
except Exception as e:
    print('Error adding result_dataset foreign key to analyst_pipelinerun:', e)

try:
    fk6 = '''ALTER TABLE `analyst_pipelinerun` 
    ADD CONSTRAINT `analyst_pipelinerun_triggered_by_id_b4c86373_fk_accounts_user_id` 
    FOREIGN KEY (`triggered_by_id`) REFERENCES `accounts_user` (`id`)'''
    cursor.execute(fk6)
    print('Triggered_by foreign key added to analyst_pipelinerun')
except Exception as e:
    print('Error adding triggered_by foreign key to analyst_pipelinerun:', e)

conn.close()