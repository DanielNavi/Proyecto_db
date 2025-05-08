#Este archivo define una funcion para obtener la conexion a tu base de datos MySQL usando PyMySQL. Puedes modificar los parametros segun lo necesites.
import pymysql

def obtener_conexion():
    return pymysql.connect(
        host="ballast.proxy.rlwy.net",
        user="root",
        password="UShYqZPcenAHzdvHcpcMoBOuuHPztGHF",
        database="railway",
        port=29681
    )

