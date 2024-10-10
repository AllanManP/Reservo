
from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for, session, flash

from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from pymongo import MongoClient
import pytz

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necesario para usar la sesión


cliente=MongoClient("mongodb+srv://allanmanriquez19:dTuYRiRENX7t8Msg@reservo.uuj9k.mongodb.net/")
app.db=cliente.reservo


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/servicios')
def servicios():
    return render_template('servicios.html')


@app.route('/salir')
def salir():
    cerrar_sesion()
    return render_template('home.html')
    
    
def cerrar_sesion():
    session.pop('cliente', None)

@app.route('/cliente')
def cliente():
    if 'cliente' not in session:
        return redirect(url_for('login', next=url_for('cliente')))
    cliente = session['cliente']
    return render_template('cliente.html', cliente=cliente)

@app.route('/modificar-cliente')
def modificarCliente():
    cliente = session['cliente']
    return render_template('modificar-cliente.html', cliente=cliente)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Verificar si el cliente ya ha iniciado sesión
    if 'cliente' in session and session['cliente']:
        return redirect(url_for('reserva'))  # Si ya ha iniciado sesión, redirigir a la página de reserva

    if request.method == 'POST':
        numero_cliente = request.form.get('numero_cliente', None)
        
        if not numero_cliente:
            flash('Por favor ingresa tu número de cliente.', 'error')
            return render_template('login.html')

        # Verificar si el número de cliente existe en la base de datos MongoDB
        cliente = app.db.clientes.find_one({"id": numero_cliente})

        if cliente:
            # Guardar los datos del cliente en la sesión
            session['cliente'] = {
                'id': cliente['id'],
                'nombre': cliente['nombre'],
                'email': cliente['email'],
                'telefono': cliente['telefono'],
                'direccion': cliente['direccion'],
                'comentarios': cliente['comentarios']
            }
            
            # Redirigir a la página de cliente si viene desde el navbar, de lo contrario a reservas
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)  # Redirigir a la página especificada en la variable 'next'
            return redirect(url_for('reserva'))  # Redirigir a reservas si no hay una página previa

        else:
            flash('Número de cliente inválido. Por favor, intente de nuevo o regístrese.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


@app.route('/recuperar-cliente', methods=['GET', 'POST'])
def recuperar():
    cerrar_sesion()
    if request.method == 'POST':
        correo_cliente = request.form['correo_cliente']

        # Verificar si el correo del cliente existe en la base de datos MongoDB
        cliente = app.db.clientes.find_one({"email": correo_cliente})
        
        if cliente:
            # Recuperar el ID del cliente
            cliente_id = cliente.get("id")
            # Implementar la recuperación del ID
            recuperar(correo_cliente, cliente_id)
            # Redirigir a la página de login con un mensaje de éxito
            flash('El ID de cliente ha sido enviado a tu correo electrónico.', 'success')
            return redirect(url_for('login'))
        else:
            # Si el cliente no existe redirigir con un mensaje de error
            flash('Correo no encontrado. Por favor, intente de nuevo o regístrese.', 'error')
            return redirect(url_for('recuperar'))  # Redirigir de nuevo a la página
        
    return render_template('recuperar-cliente.html')

def recuperar(correo_destinatario, cliente_id):
    correo_remitente = "allan.manriquez19@gmail.com"
    contraseña_remitente = "nqlr qoyx dhey ykcc"  # Usa una Contraseña de Aplicación si tienes habilitada la verificación en dos pasos

    # Crear el asunto y el cuerpo del correo
    asunto = "Recuperación N° Cliente"
    cuerpo = f"""
    Hola,

    Tu número de cliente es: {cliente_id}. 

    Saludos,
    Tu equipo de BHAS.
    """

    # Crear un objeto MIMEText
    msg = MIMEMultipart()
    msg['From'] = correo_remitente
    msg['To'] = correo_destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Inicia la conexión segura
        server.login(correo_remitente, contraseña_remitente)  # Inicia sesión en tu cuenta
        server.sendmail(correo_remitente, correo_destinatario, msg.as_string())  # Envía el correo



@app.route('/actualizar_cliente', methods=['POST'])
def actualizar_cliente():
    if 'cliente' not in session:
        return redirect(url_for('login'))  # Redirigir si no ha iniciado sesión

    # Obtener los nuevos datos del formulario
    nombre = request.form['nombre']
    email = request.form['email']
    telefono = request.form['telefono']
    direccion = request.form['direccion']
    comentarios = request.form['comentarios']

    # Actualizar los datos en la base de datos MongoDB
    cliente_id = session['cliente']['id']

    result = app.db.clientes.update_one(
        {"id": cliente_id},  # Filtrar por ID del cliente
        {
            "$set": {
                "nombre": nombre,
                "email": email,
                "telefono": telefono,
                "direccion": direccion,
                "comentarios": comentarios
            }
        }
    )

    if result.modified_count > 0:
        # Actualizar los datos de sesión con la nueva información
        session['cliente'] = {
            'id': cliente_id,
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'direccion': direccion,
            'comentarios': comentarios
        }
        flash('Perfil actualizado con éxito.', 'success')
    else:
        flash('No se realizaron cambios en el perfil.', 'info')

    return redirect(url_for('cliente'))  # Redirigir a la página del cliente


@app.route('/reserva', methods=['GET', 'POST'])
def reserva():
    # Recuperar estilistas de la base de datos MongoDB
    estilistas = list(app.db.estilistas.find({"activo": 1}))  # Filtrar estilistas activos
    
    if request.method == 'POST':
        nombre = request.form['name']
        email = request.form['email']
        telefono = request.form['phone']
        direccion = request.form['address']
        comentarios = request.form['comments']
        estilista = request.form['stylist']
        servicio = request.form['service']
        #print(estilista)
        nom_estilista=estilista
        # Verificar si el cliente ya existe en MongoDB
        cliente = app.db.clientes.find_one({"email": email})

        if cliente:
            # El cliente ya existe, obtener su ID
            cliente_id = cliente['id']
        else:
            # Generar ID personalizado usando las iniciales del nombre completo y un contador
            iniciales = ''.join([parte[0].upper() for parte in nombre.split()])

            # Obtener el conteo de clientes existentes con las mismas iniciales
            count = app.db.clientes.count_documents({"id": {"$regex": f"^{iniciales}"}}) + 1  # Incrementar el contador para que sea único

            # Construir el ID final con las iniciales y el contador
            cliente_id = f"{iniciales}{count}"

            # Insertar el nuevo cliente en la base de datos MongoDB
            app.db.clientes.insert_one({
                "id": cliente_id,
                "nombre": nombre,
                "email": email,
                "direccion": direccion,
                "telefono": telefono,
                "comentarios": comentarios
            })

            # Enviar correo electrónico de agradecimiento
            enviar_correo_agradecimiento(email, nombre, cliente_id)

        # Guardar datos del cliente en la sesión
        session['cliente'] = {
            'id': cliente_id,
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'direccion': direccion,
            'comentarios': comentarios
        }

        # Obtener el ID del estilista seleccionado
        idestilista = app.db.estilistas.find_one({"nombre": estilista})
        # Guardar el estilista y servicio seleccionados en la sesión
        session['reserva'] = {
            'estilista': {'id': idestilista['id']},  # Almacena el ID como parte de un diccionario
            'servicio': servicio
        }

        return redirect(url_for('calendario',nom_estilista=nom_estilista, idestilista=idestilista['id']))
    
    return render_template('reserva.html', estilistas=estilistas)


def enviar_correo_agradecimiento(correo_destinatario, nombre, cliente_id):
    correo_remitente = "allan.manriquez19@gmail.com"
    contraseña_remitente = "nqlr qoyx dhey ykcc"  # Usa una Contraseña de Aplicación si tienes habilitada la verificación en dos pasos

    # Crear el asunto y el cuerpo del correo
    asunto = "Gracias por Registrarte"
    cuerpo = f"""
    Hola {nombre},

    Gracias por registrarte en Beauty Hair Anais Studio. Tu ID de cliente es: {cliente_id}. 

    Con este ID, puedes iniciar sesión para hacer futuras reservas.

    ¡Esperamos verte pronto!

    Saludos,
    Tu equipo de BHAS.
    """

    # Crear un objeto MIMEText
    msg = MIMEMultipart()
    msg['From'] = correo_remitente
    msg['To'] = correo_destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Inicia la conexión segura
        server.login(correo_remitente, contraseña_remitente)  # Inicia sesión en tu cuenta
        server.sendmail(correo_remitente, correo_destinatario, msg.as_string())  # Envía el correo

@app.route('/calendario', methods=['GET', 'POST'])
def calendario():
    estilista_dict = session.get('reserva', {}).get('estilista')
    estilista_id = request.args.get('idestilista')
    #obtener nom_estilista de los args
    nom_estilista=request.args.get('nom_estilista')


    # Consultar la disponibilidad del estilista en MongoDB
    disponibilidad_data = list(app.db.disponibilidad.find({
        "estilista_id": estilista_id,
        "fecha": {"$gte": datetime.now(), "$lt": datetime.now() + timedelta(days=7)}
    }))

    # Ordenar la disponibilidad por fecha y hora
    disponibilidad_data.sort(key=lambda x: (x['fecha'], x['hora']))  # Ordenar por fecha y hora

    # Debugging: Imprimir los datos recuperados
    #print("Datos de disponibilidad:", disponibilidad_data)

    if not disponibilidad_data:
        print("No se encontró disponibilidad para este estilista.")
        # Puedes manejar este caso de manera apropiada, como enviar un mensaje a la plantilla

    disponibilidad = {}
    
    # Procesar la disponibilidad por fecha y horas
    for item in disponibilidad_data:
        fecha_str = item['fecha'].strftime('%Y-%m-%d')  # Convertir fecha a string
        if fecha_str not in disponibilidad:
            disponibilidad[fecha_str] = []
        
        # Asegúrate de que la hora esté en el formato correcto
        disponibilidad[fecha_str].append({
        'hora': item['hora'],
        '_id': str(item['_id'])  # Convertir el ObjectId a string
        })

    if request.method == 'POST':
        id_estilista=session.get('reserva', {}).get('estilista').get('id')
        servicio = session.get('reserva', {}).get('servicio')
        fecha = request.form['fecha']
        hora_seleccionada= request.form['hora']
        id_disponibilidad = request.form['id_disponibilidad']
        print('id_disponibilidad',id_disponibilidad)
        #sumar 1 hora a la hora_seleccionada para obtener la hora_final
        hora_final = datetime.strptime(hora_seleccionada, '%H:%M') + timedelta(hours=1)
        hora_final_str = hora_final.strftime('%H:%M')
        #print('hora seleccionada',hora_seleccionada,' hora_final',hora_final_str,'fecha',fecha,' cliente',session['cliente']['id'],'servicio',servicio,'idestilista',id_estilista)
        #insertar la cita en la base de datos MongoDB
        resultado_insercion =app.db.cita.insert_one({
            "idcita": ObjectId(),
            "idestilista": id_estilista,
            "servicio": servicio,
            "fecha": fecha,
            "hora_inicio": hora_seleccionada,
            "hora_final": hora_final_str,
            "cliente_id": session['cliente']['id']
        })
        
        #obtener el idcita que se acaba de insertar la base de datos MongoDB
        idcita = resultado_insercion.inserted_id
        #print("ID de la cita insertada:", idcita)
        # Guardar la cita en la sesión
        session['cita'] = {
            'idcita': str(idcita),
            "idestilista": id_estilista,
            "servicio": servicio,
            "fecha": fecha,
            "hora_inicio": hora_seleccionada,
            "hora_final": hora_final_str,
            "cliente_id": session['cliente']['id']
        }
        return redirect(url_for('confirmacion', idcita=idcita, id_disponibilidad=id_disponibilidad))

    # Renderizar la plantilla del calendario con la disponibilidad y el ID del estilista
    return render_template('calendario.html', disponibilidad=disponibilidad, estilista=estilista_id, nom_estilista=nom_estilista )




@app.route('/confirmacion')
def confirmacion():
    idcita = request.args.get('idcita')
    id_disponibilidad= request.args.get('id_disponibilidad')
    # Verificar si se proporcionó un idcita válido
    if not idcita:
        return "Error: No se proporcionó un ID de cita válido."
    
    try:
        # Convertir idcita a ObjectId para buscarlo en MongoDB
        idcita = ObjectId(idcita)
    except Exception as e:
        return f"Error: ID de cita inválido ({str(e)})"
    
    # Obtener la información de la cita desde MongoDB utilizando _id
    cita_info = app.db.cita.find_one({"_id": idcita})
    
    if not cita_info:
        return "Error: No se encontró la cita con el ID proporcionado."
    
     # Extraer el id del cliente y del estilista de la cita
    cliente_id = cita_info.get('cliente_id')
    estilista_id = cita_info.get('idestilista')
    
    # Obtener la información del cliente desde la colección "clientes"
    cliente_info = app.db.clientes.find_one({"id": cliente_id})
    
    if not cliente_info:
        return "Error: No se encontró el cliente con el ID proporcionado."
    
    # Obtener la información del estilista desde la colección "estilistas"
    estilista_info = app.db.estilistas.find_one({"id": estilista_id})
    
    if not estilista_info:
        return "Error: No se encontró el estilista con el ID proporcionado."
    
    # Información del cliente y estilista
    nombre_cliente = cliente_info.get('nombre')
    correo_cliente = cliente_info.get('email')
    nombre_estilista = estilista_info.get('nombre')
      
    
    # Obtener la información del cliente desde la sesión
    correo_destinatario = session['cliente']['email']
    nombre = session['cliente']['nombre']
    fecha = session['cita']['fecha']
    hora_inicio = session['cita']['hora_inicio']
    enviar_correo_confirmacion(correo_destinatario, nombre, fecha,hora_inicio)
    eliminar_disponibilidad(id_disponibilidad)
    # Renderizar la página de confirmación con los detalles de la cita
    return render_template('confirmacion.html', cita=cita_info,nombre_cliente=nombre_cliente, nombre_estilista=nombre_estilista)


def enviar_correo_confirmacion(correo_destinatario, nombre, fecha,hora):
    correo_remitente = "allan.manriquez19@gmail.com"
    contraseña_remitente = "nqlr qoyx dhey ykcc"  # Usa una Contraseña de Aplicación si tienes habilitada la verificación en dos pasos

    # Crear el asunto y el cuerpo del correo
    asunto = "Cita agendada"
    cuerpo = f"""
    Estimad@ {nombre},

    Su cita ha sido agendada con exito: 
    Fecha: {fecha}
    Hora: {hora}
    Gracias por preferirnos.

    Saludos,
    Equipo de BHAS.
    """

    # Crear un objeto MIMEText
    msg = MIMEMultipart()
    msg['From'] = correo_remitente
    msg['To'] = correo_destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Inicia la conexión segura
        server.login(correo_remitente, contraseña_remitente)  # Inicia sesión en tu cuenta
        server.sendmail(correo_remitente, correo_destinatario, msg.as_string())  # Envía el correo




def eliminar_disponibilidad(id_disponibilidad):
    # Asegúrate de convertir el id a ObjectId
    try:
        id_disponibilidad_obj = ObjectId(id_disponibilidad)
    except Exception as e:
        print(f"Error al convertir el ID a ObjectId: {str(e)}")
        return

    # Buscar y eliminar el documento de disponibilidad
    resultado = app.db.disponibilidad.delete_one({"_id": id_disponibilidad_obj})
    
    if resultado.deleted_count > 0:
        print("Disponibilidad eliminada con éxito.")
    else:
        print("No se encontró ninguna disponibilidad con ese ID.")



    










#Administrador
@app.route('/admin/generar_disponibilidad', methods=['GET', 'POST'])
def generar_disponibilidad():
    return render_template('generar_disponibilidad.html')


@app.route('/crear_disponibilidad', methods=['GET', 'POST'])
def crear_disponibilidad():
    if request.method == 'POST':
        estilista_id = request.form['estilista_id']
        fecha_str = request.form['fecha']
        hora_inicio_str = request.form['hora_inicio']
        hora_fin_str = request.form['hora_fin']

        # Convertir las fechas y horas en objetos datetime
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()

        # Crear una lista de las horas disponibles entre hora_inicio y hora_fin
        horas_disponibles = []
        hora_actual = datetime.combine(fecha, hora_inicio)

        while hora_actual.time() < hora_fin:
            horas_disponibles.append(hora_actual.time().strftime('%H:%M'))
            hora_actual += timedelta(hours=1)  # Incrementar por horas completas

        # Insertar las horas disponibles en la colección 'disponibilidad' en MongoDB
        for hora in horas_disponibles:
            app.db.disponibilidad.insert_one({
                "estilista_id": estilista_id,
                "fecha": fecha,
                "hora": hora
            })

        # Redirigir a una página de confirmación o a otra página
        return redirect(url_for('generar_disponibilidad'))

    return render_template('generar_disponibilidad.html')



if __name__ == '__main__':
    app.run(debug=True,port=5000)