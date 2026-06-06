import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Create the analyst_analystbase table
sql = '''
CREATE TABLE `analyst_analystbase` (
  `id` uuid NOT NULL PRIMARY KEY,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `category` varchar(50) NOT NULL,
  `schema` json NOT NULL,
  `row_count` integer NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `dataset_id` uuid NULL UNIQUE,
  `created_by_id` bigint NOT NULL
)
'''
try:
    cursor.execute(sql)
    print('Table analyst_analystbase created successfully')
except Exception as e:
    print('Error creating analyst_analystbase table:', e)

# Add foreign key constraints
try:
    fk1 = '''ALTER TABLE `analyst_analystbase` 
    ADD CONSTRAINT `analyst_analystbase_dataset_id_50e68ce9_fk_analyst_s` 
    FOREIGN KEY (`dataset_id`) REFERENCES `analyst_storeddataset` (`id`)'''
    cursor.execute(fk1)
    print('Dataset foreign key added successfully')
except Exception as e:
    print('Error adding dataset foreign key:', e)

try:
    fk2 = '''ALTER TABLE `analyst_analystbase` 
    ADD CONSTRAINT `analyst_analystbase_created_by_id_4f565a16_fk_accounts_user_id` 
    FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`)'''
    cursor.execute(fk2)
    print('Created_by foreign key added successfully')
except Exception as e:
    print('Error adding created_by foreign key:', e)

conn.close()