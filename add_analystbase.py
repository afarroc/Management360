import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Add analyst_base column to analyst_etlsource (for migration 0008)
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` ADD COLUMN `analyst_base` uuid NULL')
    print('Column analyst_base added to analyst_etlsource')
except Exception as e:
    print('Error adding analyst_base column:', e)

# Add foreign key constraint for analyst_base
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` ADD CONSTRAINT `analyst_etlsource_analyst_base_id_24a94e80_fk_analyst_a` FOREIGN KEY (`analyst_base`) REFERENCES `analyst_analystbase` (`id`)')
    print('Foreign key constraint added for analyst_base')
except Exception as e:
    print('Error adding foreign key constraint for analyst_base:', e)

conn.close()