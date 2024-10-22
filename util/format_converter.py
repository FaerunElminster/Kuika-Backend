from datetime import datetime

def convert_to_datetime(date_string):
    # Türkçe ay isimlerini datetime için tanımlama
    months = {
        'Ocak': 'January', 'Şubat': 'February', 'Mart': 'March',
        'Nisan': 'April', 'Mayıs': 'May', 'Haziran': 'June',
        'Temmuz': 'July', 'Ağustos': 'August', 'Eylül': 'September',
        'Ekim': 'October', 'Kasım': 'November', 'Aralık': 'December'
    }

    # Tarihi parçalarına ayırma
    day, month_tr, year = date_string.split()

    # Türkçe ay ismini İngilizce'ye çevirme
    month_en = months[month_tr]

    # String'i datetime formatına dönüştürme
    date_object = datetime.strptime(f"{day} {month_en} {year}", "%d %B %Y")
    return date_object