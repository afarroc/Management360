import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Add sim_account column to analyst_etlsource (for migration 0013)
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` ADD COLUMN `sim_account` uuid NULL')
    print('Column sim_account added to analyst_etlsource')
except Exception as e:
    print('Error adding sim_account column:', e)

# Add events_model column to analyst_etlsource (for migration 0014)
try:
    cursor.execute("ALTER TABLE `analyst_etlsource` ADD COLUMN `events_model` varchar(20) NOT NULL DEFAULT ''")
    print('Column events_model added to analyst_etlsource')
except Exception as e:
    print('Error adding events_model column:', e)

# Add foreign key constraint for sim_account
try:
    cursor.execute('ALTER TABLE `analyst_etlsource` ADD CONSTRAINT `analyst_etlsource_sim_account_id_XXXXXX` FOREIGN KEY (`sim_account`) REFERENCES `sim_simaccount` (`id`)')
    print('Foreign key constraint added for sim_account')
except Exception as e:
    print('Error adding foreign key constraint for sim_account:', e)

conn.close()