import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Run the exact ALTER TABLE statements from Django
statements = [
    'ALTER TABLE `analyst_crosssource` ADD CONSTRAINT `analyst_crosssource_last_result_id_db77eed3_fk_analyst_s` FOREIGN KEY (`last_result_id`) REFERENCES `analyst_storeddataset` (`id`)',
    'ALTER TABLE `analyst_crosssource` ADD CONSTRAINT `analyst_crosssource_created_by_id_9720e6dd_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`)'
]

for i, sql in enumerate(statements, 1):
    try:
        cursor.execute(sql)
        print(f'Statement {i} executed successfully')
    except Exception as e:
        print(f'Error executing statement {i}: {e}')

conn.close()