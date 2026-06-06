import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Drop the foreign key constraint on the column sim_account
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` DROP FOREIGN KEY `analyst_etlsource_sim_account_id_XXXXXX`')
    print('Dropped foreign key constraint analyst_etlsource_sim_account_id_XXXXXX')
except Exception as e:
    print('Error dropping foreign key constraint:', e)

# Rename the column from sim_account to sim_account_id
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` CHANGE `sim_account` `sim_account_id` uuid NULL')
    print('Renamed column sim_account to sim_account_id')
except Exception as e:
    print('Error renaming column:', e)

# Add foreign key constraint on sim_account_id
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` ADD CONSTRAINT `analyst_etlsource_sim_account_id_XXXXXX` FOREIGN KEY (`sim_account_id`) REFERENCES `sim_simaccount` (`id`)')
    print('Added foreign key constraint on sim_account_id')
except Exception as e:
    print('Error adding foreign key constraint on sim_account_id:', e)

conn.close()