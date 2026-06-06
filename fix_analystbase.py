import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Drop the foreign key constraint first
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` DROP FOREIGN KEY `analyst_etlsource_analyst_base_id_24a94e80_fk_analyst_a`')
    print('Dropped foreign key constraint analyst_etlsource_analyst_base_id_24a94e80_fk_analyst_a')
except Exception as e:
    print('Error dropping foreign key constraint:', e)

# Drop the incorrect column analyst_base
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` DROP COLUMN `analyst_base`')
    print('Dropped incorrect column analyst_base')
except Exception as e:
    print('Error dropping analyst_base column:', e)

# Add the correct column analyst_base_id (as per migration 0008)
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` ADD COLUMN `analyst_base_id` uuid NULL')
    print('Added correct column analyst_base_id')
except Exception as e:
    print('Error adding analyst_base_id column:', e)

# Add foreign key constraint for analyst_base_id
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` ADD CONSTRAINT `analyst_etlsource_analyst_base_id_24a94e80_fk_analyst_a` FOREIGN KEY (`analyst_base_id`) REFERENCES `analyst_analystbase` (`id`)')
    print('Foreign key constraint added for analyst_base_id')
except Exception as e:
    print('Error adding foreign key constraint for analyst_base_id:', e)

conn.close()