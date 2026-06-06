import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Add the missing data_blob column to analyst_storeddataset
try:
    cursor.execute('ALTER TABLE `analyst_storeddataset` ADD COLUMN `data_blob` longtext NOT NULL DEFAULT ""')
    print('Added data_blob column to analyst_storeddataset table')
except Exception as e:
    print('Error adding data_blob column:', e)

# Verify the column was added
cursor.execute('DESCRIBE analyst_storeddataset')
print('\nUpdated analyst_storeddataset table structure:')
for row in cursor.fetchall():
    print(row)

conn.close()