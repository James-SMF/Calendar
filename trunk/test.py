from datetime import datetime

# 示例列表
date_list = ['2024_01', '2023_12', '2024_03', '2023_11', '2024_02']

# 按照时间排序
sorted_list = sorted(date_list, key=lambda date: datetime.strptime(date, '%Y_%m'), reverse=True)

# 打印排序结果
print(sorted_list)

