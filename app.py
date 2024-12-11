
from bson import ObjectId
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash

from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from pymongo import MongoClient

import pytz

from werkzeug.utils import secure_filename
import os
from bson.objectid import ObjectId


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necesario para usar la sesión

mongo_uri = os.getenv("MONGO_URI")
cliente = MongoClient(mongo_uri)
#cliente = MongoClient("mongodb+srv://allanmanriquez19:dTuYRiRENX7t8Msg@reservo.uuj9k.mongodb.net/")

app.db=cliente.reservo
servicios_collection = app.db['servicios']


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/servicios')
def servicios():
    servicios = list(servicios_collection.find())
    return render_template('servicios.html', servicios=servicios)


@app.route('/salir')
def salir():
    cerrar_sesion()
    return render_template('home.html')
    
    
def cerrar_sesion():
    session.pop('cliente', None)
    session.pop('estilista', None)
    session.pop('admin', None)

@app.route('/cliente')
def cliente():
    # Verificar si el cliente ha iniciado sesión
    if 'cliente' not in session:
        message="Debes iniciar sesión primero."
        return render_template('login.html',message)  # Si no está en sesión, redirigir al login
    
    # Obtener los datos del cliente desde la sesión
    cliente = session['cliente']
    cliente_id = cliente['id']  # Accedemos al id del cliente desde la sesión
    
    # Buscar los datos del cliente en la base de datos MongoDB usando el id
    cliente_db = app.db.clientes.find_one({"id": cliente_id})

    if not cliente_db:
        message="Cliente no encontrado."
        return render_template('login.html',message)  # Si no se encuentra el cliente en la base de datos, redirigir al login
    
    # Obtener las citas finalizadas del cliente desde la base de datos
    citas = app.db.cita_finalizada.find({"id_cliente": cliente_id})

    # Convertimos el cursor de MongoDB a una lista
    citas = list(citas)

    message = request.args.get('message')  # Obtén el mensaje de los parámetros de la URL
    return render_template('cliente.html', cliente=cliente_db, citas=citas, message=message)


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
            message="Por favor ingresa tu número de cliente."
            return render_template('login.html',message=message)

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
            message="Número de cliente inválido. Por favor, intente de nuevo o regístrese."
            return render_template('login.html',message=message)
    
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
            message="El ID de cliente ha sido enviado a tu correo electrónico."
            return render_template('login.html',message=message)
        else:
            # Si el cliente no existe redirigir con un mensaje de error
            message="Correo no encontrado. Por favor, intente de nuevo o regístrese."
            return render_template('recuperar-cliente.html',message=message)  # Redirigir de nuevo a la página
        
    return render_template('recuperar-cliente.html')

def recuperar(correo_destinatario, cliente_id):
    correo_remitente = "bhanais.studio@gmail.com"
    contraseña_remitente = "yfrx psyz nosf uirf"  # Usa una Contraseña de Aplicación si tienes habilitada la verificación en dos pasos

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
        message='Perfil actualizado con éxito.'
    else:
        message='No se realizaron cambios en el perfil.'

    return redirect(url_for('cliente',message=message))  # Redirigir a la página del cliente


@app.route('/reserva', methods=['GET', 'POST'])
def reserva():
    # Recuperar estilistas de la base de datos MongoDB
    estilistas = list(app.db.estilistas.find({"activo": 1}))  # Filtrar estilistas activos
    servicios = list(servicios_collection.find())  # Recupera todos los servicios
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
    
    return render_template('reserva.html', estilistas=estilistas,servicios=servicios)
def enviar_correo_agradecimiento(correo_destinatario, nombre, cliente_id):
    correo_remitente = "bhanais.studio@gmail.com"
    contraseña_remitente = "yfrx psyz nosf uirf"  # Usa una Contraseña de Aplicación si tienes habilitada la verificación en dos pasos

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

def enviar_correo_aviso(correo_destinatario, nombre):
    correo_remitente = "bhanais.studio@gmail.com"
    contraseña_remitente = "yfrx psyz nosf uirf"  # Usa una Contraseña de Aplicación si tienes habilitada la verificación en dos pasos

    # Crear el asunto y el cuerpo del correo
    asunto = "¡Hemos cancelado su cita!"
    cuerpo = f"""
    Hola {nombre},

    Debido a razones de fuerza mayor debimos cancelar su cita. 

    Te invitamos a agendar una cita en un diferente dia.

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

    sin_disponibilidad = not disponibilidad_data
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
            "cliente_id": session['cliente']['id'],
            "estado": "Pendiente"
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
    return render_template(
        'calendario.html',
        disponibilidad=disponibilidad,
        estilista=estilista_id,
        nom_estilista=nom_estilista,
        sin_disponibilidad=sin_disponibilidad
    )
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
    correo_remitente = "bhanais.studio@gmail.com"
    contraseña_remitente = "yfrx psyz nosf uirf"  # Usa una Contraseña de Aplicación si tienes habilitada la verificación en dos pasos

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



#----------------------------------------
# Reseña


@app.route('/resena', methods=['GET'])
def resena():
    reviews = list(app.db.reviews.find())
    # Convertir ObjectId a string
    for review in reviews:
        review['_id'] = str(review['_id'])
    message = request.args.get('message')
    print(reviews)  # Depuración
    return render_template('resena.html', reviews=reviews,message=message)

@app.route('/resena_cliente', methods=['GET'])
def resena_cliente():
    reviews = list(app.db.reviews.find())
    # Convertir ObjectId a string
    for review in reviews:
        review['_id'] = str(review['_id'])
    
    print(reviews)  # Depuración
    return render_template('resena_cliente.html', reviews=reviews)

@app.route('/enviar_resena', methods=['POST'])
def enviar_resena():
    if 'cliente' in session:
        try:
            rating = int(request.form['rating'])
            comment = request.form['comment']
            nombre=session['cliente']['nombre']
            # Aquí puedes guardar la reseña en la base de datos o en una lista
            nueva_resena = {'rating': rating, 'comment': comment,'nombre':nombre}

            # Supongamos que tienes una lista para almacenar las reseñas
            #reviews = app.db.reviews
            app.db.reviews.insert_one({
                'rating': rating, 
                'comment': comment,
                'nombre':nombre,
                'creacion': datetime.now().strftime('%d-%m-%Y'),
            })
            # Renderiza la página con las nuevas reseñas
            return redirect(url_for('resena'))
        except KeyError:
            return redirect(url_for('resena'))
    else:
        message="Debes iniciar sesión para enviar una reseña."
        return redirect(url_for('resena',message=message))


@app.route('/enviar_resena_cliente', methods=['POST'])
def enviar_resena_cliente():
    if 'cliente' in session:
        try:
            rating = int(request.form['rating'])
            comment = request.form['comment']
            nombre=session['cliente']['nombre']
            # Aquí puedes guardar la reseña en la base de datos o en una lista
            nueva_resena = {'rating': rating, 'comment': comment,'nombre':nombre}

            # Supongamos que tienes una lista para almacenar las reseñas
            #reviews = app.db.reviews
            app.db.reviews.insert_one({
                'rating': rating, 
                'comment': comment,
                'nombre':nombre,
                'creacion': datetime.now().strftime('%d-%m-%Y'),
            })
            # Renderiza la página con las nuevas reseñas
            return redirect(url_for('resena_cliente'))
        except KeyError:
            return redirect(url_for('resena_cliente'))
    else:
        message="Debes iniciar sesión para enviar una reseña."
        return redirect(url_for('resena_cliente',message=message))

from bson import ObjectId

@app.route('/responder_resena/<resena_id>', methods=['POST'])
def responder_resena(resena_id):
    # Convertir resena_id de string a ObjectId para buscarlo en MongoDB
    resena_object_id = ObjectId(resena_id)

    # Lógica para buscar la reseña por ObjectId y añadir la respuesta del admin
    review = app.db.reviews.find_one({"_id": resena_object_id})
    if review:
        # Actualizar la reseña con la respuesta del administrador
        respuesta = request.form.get('respuesta')
        app.db.reviews.update_one(
            {"_id": resena_object_id},
            {"$set": {"respuesta": respuesta}}
        )
        message='Respuesta añadida con éxito'
    else:
        message='Reseña no encontrada'

    return redirect(url_for('resena',message=message))
@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        try:
            # Imprimir los datos del formulario para depurar
            print(request.form)  # Esto mostrará los datos recibidos en la consola

            # Acceder a los datos del formulario
            nombre = request.form['nombre']
            email = request.form['email']
            telefono = request.form['telefono']
            mensaje = request.form['mensaje']

            # Enviar el correo
            enviar_correo_contacto(nombre,email,telefono,mensaje)

            return render_template('contacto_mail.html')  # Muestra una confirmación
        except KeyError as e:
            print(f"KeyError: {e}")  # Para saber cuál clave está causando el problema
            return f"Faltan datos en el formulario: {e}", 400  # Indica qué dato falta
        except Exception as e:
            print(f"Ocurrió un error: {e}")  # Captura otros errores
            return "Ocurrió un error al enviar el correo", 500
    else:
        # Si es un GET, simplemente muestra el formulario
        return render_template('contacto.html')


def enviar_correo_contacto(nombre,email,telefono,mensaje):
    correo_remitente = "bhanais.studio@gmail.com"
    contraseña_remitente = "yfrx psyz nosf uirf"  # Usa una Contraseña de Aplicación si tienes habilitada la verificación en dos pasos

    # Crear el asunto y el cuerpo del correo
    asunto = "Nuevo mensaje de contacto"
    cuerpo = f"""Nombre: {nombre}\nEmail: {email}\nTeléfono: {telefono}\nMensaje: {mensaje}"""

    # Crear un objeto MIMEText
    msg = MIMEMultipart()
    msg['From'] = correo_remitente
    msg['To'] = correo_remitente
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Inicia la conexión segura
        server.login(correo_remitente, contraseña_remitente)  # Inicia sesión en tu cuenta
        server.sendmail(correo_remitente, correo_remitente, msg.as_string())  # Envía el correo






#Administrador

def validate_login(username, password):
    # Buscar los detalles del administrador con base en el nombre de usuario
    admin = app.db.admin.find_one({"correo": username})
    
    if not admin:
        return False, "Usuario o contraseña incorrectos."
    
    # Comparar la contraseña (aquí texto plano, pero se debería usar hash en un escenario real)
    if password != admin['pass']:  # Idealmente usar check_password_hash para contraseñas encriptadas
        return False, "Usuario o contraseña incorrectos."
    
    return True, admin

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    cerrar_sesion()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validar credenciales
        valid, result = validate_login(username, password)
        
        if not valid:
            error = result  # Credenciales incorrectas
        else:
            # Almacenar la información del usuario en la sesión
            
            # Redireccionar según el rol del usuario
            if result['rol'] == 'admin':
                session['admin'] = {
                    '_id': str(result['_id']),
                    'correo': result['correo'],
                    'rol': result['rol'],
                    'idestilista': result['idestilista']
                }
                return redirect(url_for('admin_inicio'))  # Redirigir a la página de inicio de administradores
            elif result['rol'] == 'estilista':
                session['estilista'] = {
                    '_id': str(result['_id']),
                    'correo': result['correo'],
                    'rol': result['rol'],
                    'idestilista': result['idestilista']
                }
                return redirect(url_for('estilista_inicio'))  # Redirigir a la página de inicio de estilistas
    
    return render_template('admin_login.html', error=error)

@app.route('/logout')
def logout():
    cerrar_sesion()  # Elimina la sesión del administrador
    return render_template('admin_login.html')  # Redirige a la página de inicio de sesión

@app.route('/admin/inicio')
def admin_inicio():
    # Verifica si el usuario es admin
    if 'admin' in session:
        return render_template('admin_inicio.html')
    return redirect(url_for('admin_login'))  # Redirige si no hay sesión o no es admin

@app.route('/estilista/inicio')
def estilista_inicio():
    # Verifica si el usuario es estilista
    if 'estilista' in session:
        return render_template('admin_inicio.html')
    return redirect(url_for('admin_login'))  # Redirige si no hay sesión o no es estilista

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session or session['admin']['rol'] != 'admin':
        return redirect(url_for('admin_login'))
    return "¡Bienvenido, Administrador! Tienes acceso total."

# Ruta para el panel de estilistas
@app.route('/stylist/dashboard')
def stylist_dashboard():
    if 'admin' not in session or session['admin']['rol'] != 'estilista':
        return redirect(url_for('admin_login'))
    return "¡Bienvenido, Estilista! Tienes acceso restringido."

@app.route('/admin/generar_disponibilidad', methods=['GET', 'POST'])
def generar_disponibilidad_admin():
    if 'admin' not in session or session['admin']['rol'] != 'admin':
        return redirect(url_for('admin_login'))
    else:
        estilistas = list(app.db.estilistas.find())
        return render_template('generar_disponibilidad.html', estilista=estilistas)

@app.route('/estilista/crear_disponibilidad', methods=['GET', 'POST'])
def generar_disponibilidad_estilista():
    if 'estilista' not in session or session['estilista']['rol'] != 'estilista':
        return redirect(url_for('admin_login'))
    else:
        
        estilistas = list(app.db.estilistas.find())
        return render_template('generar_disponibilidad.html', estilista=estilistas)

@app.route('/generar_disponibilidad', methods=['GET', 'POST'])
def generar_disponibilidad():
    if 'estilista' in session and session['estilista']['rol'] == 'estilista':
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

            # Comprobar que no exista fecha y estilista_id en la colección 'disponibilidad' en MongoDB
            if app.db.disponibilidad.find_one({
                "estilista_id": estilista_id,
                "fecha": fecha
            }):
                estilistas = list(app.db.estilistas.find())
                return render_template('generar_disponibilidad.html', estilista=estilistas, error="La fecha y hora seleccionada ya están ocupadas.")
            else:
                # Comprobar que la disponibilidad del estilista no superponga con otras horas en la misma fecha
                # Insertar las horas disponibles en la colección 'disponibilidad' en MongoDB
                for hora in horas_disponibles:
                    app.db.disponibilidad.insert_one({
                        "estilista_id": estilista_id,
                        "fecha": fecha,
                        "hora": hora
                    })
                estilistas = list(app.db.estilistas.find())
                return render_template('generar_disponibilidad.html', estilista=estilistas, success="Fecha y Horas agregadas a disponibilidad")
        estilistas = list(app.db.estilistas.find())
        return render_template('generar_disponibilidad.html', estilista=estilistas)

    elif 'admin' in session and session['admin']['rol'] == 'admin':
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

            # Comprobar que no exista fecha y estilista_id en la colección 'disponibilidad' en MongoDB
            if app.db.disponibilidad.find_one({
                "estilista_id": estilista_id,
                "fecha": fecha
            }):
                estilistas = list(app.db.estilistas.find())
                return render_template('generar_disponibilidad.html', estilista=estilistas, error="La fecha y hora seleccionada ya están ocupadas.")
            else:
                # Insertar las horas disponibles en la colección 'disponibilidad' en MongoDB
                for hora in horas_disponibles:
                    app.db.disponibilidad.insert_one({
                        "estilista_id": estilista_id,
                        "fecha": fecha,
                        "hora": hora
                    })
                estilistas = list(app.db.estilistas.find())
                # Redirigir a una página de confirmación o a otra página
                return render_template('generar_disponibilidad.html', estilista=estilistas, success="Fecha y Horas agregadas a disponibilidad")

        return render_template('generar_disponibilidad.html')
    
    else:
        # Redirigir a la página de login si no hay sesión válida
        return redirect(url_for('admin_login'))

@app.route('/admin_servicios')
def admin_servicios():
    servicios = list(servicios_collection.find())  # Recupera todos los servicios
    message = request.args.get('message')
    return render_template('admin_servicios.html', servicios=servicios, message=message)


# Ruta para modificar un servicio (mostrar formulario y actualizar)
@app.route('/admin/servicios/modificar/<int:id>', methods=['GET', 'POST'])
def modificar_servicio(id):
    # Buscar el servicio por el campo "id"
    servicio = servicios_collection.find_one({"id": id})
    
    if not servicio:
        return redirect(url_for('admin_servicios'))

    if request.method == 'POST':
        # Obtiene los datos actualizados del formulario
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        
        # Manejar la carga de la nueva imagen (opcional)
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename != '':
                # Guardar la nueva imagen en el servidor
                foto.save(os.path.join('static/img/cortes', foto.filename))
                img_url = f"/static/img/cortes/{foto.filename}"
            else:
                img_url = servicio['img_url']  # Usar la imagen existente si no se proporciona una nueva
        else:
            img_url = servicio['img_url']  # Usar la imagen existente si no se proporciona una nueva

        # Actualiza el servicio en la base de datos
        servicios_collection.update_one(
            {"id": id},  # Buscar por el campo "id"
            {"$set": {
                "nombre": nombre,
                "descripcion": descripcion,
                "img_url": img_url  # Actualizar el campo de imagen
            }}
        )
        message="Servicio actualizado con éxito."
        return redirect(url_for('admin_servicios',message=message))

    return render_template('modificar_servicio.html', servicio=servicio)



# Ruta para eliminar un servicio
@app.route('/admin/servicios/eliminar/<string:id>')
def eliminar_servicio(id):
    servicio = servicios_collection.find_one({"_id": int(id)})
    if servicio:
        servicios_collection.delete_one({"_id": int(id)})
        message="Servicio eliminado con éxito."
    else:
        message="Servicio no encontrado."

    return redirect(url_for('admin_servicios',message=message))




# Asegúrate de tener configurada tu colección de servicios
# servicios_collection = ... (configura tu conexión a la base de datos)
@app.route('/admin/servicios/agregar', methods=['GET', 'POST'])
def agregar_servicio():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']

        # Manejar la carga de la imagen
        if 'foto' not in request.files:
            message='No se ha seleccionado ninguna imagen.'
            return redirect(request.url)
        
        foto = request.files['foto']
        
        if foto.filename == '':
            message='No se ha seleccionado ninguna imagen.'
            return redirect(request.url)

        # Guardar la imagen en el servidor
        foto.save(os.path.join('static/img/cortes', foto.filename))
        img_url = f"/static/img/cortes/{foto.filename}"

        # Obtener el último servicio para definir el nuevo ID
        last_servicio = servicios_collection.find_one(sort=[("id", -1)])  # Obtener el servicio con el ID más alto
        
        # Comprobar si el último servicio tiene un ID válido
        if last_servicio and 'id' in last_servicio:
            new_id = last_servicio['id'] + 1  # Incrementar el ID
        else:
            new_id = 1  # Comenzar en 1 si no hay servicios

        # Guardar el servicio en la base de datos con un ID automático como Integer
        servicios_collection.insert_one({
            "_id": new_id,  # Definir _id manualmente como Integer
            "id": new_id,
            "nombre": nombre,
            "descripcion": descripcion,
            "img_url": img_url
        })
        message="Servicio agregado correctamente."
        return redirect(url_for('admin_servicios',message=message))  # Asegúrate de que 'admin_servicios' esté definido

    return render_template('agregar_servicio.html')


@app.route('/admin/servicios/<id>', methods=['GET'])
def ver_servicio(id):
    # Obtener el servicio por ID
    servicio = servicios_collection.find_one({"_id": int(id)})
    if servicio is None:
        message="Servicio no encontrado."
        return redirect(url_for('admin_servicios'))
    
    return render_template('ver_servicio.html', servicio=servicio,message=message)


#------------------------------------------------
# ADMIN_ESTILISTAS
#------------------------------------------------
@app.route('/admin/estilistas')
def admin_estilistas():
    if 'admin' not in session or session['admin']['rol'] != 'admin':
        return redirect(url_for('admin_login'))
    else:
        estilistas = app.db.estilistas.find()
        lista_estilistas = []
        for estilista in estilistas:
            estilista['telefono'] = str(estilista['telefono'])  # Convertimos a cadena si es necesario
            lista_estilistas.append(estilista)
        message = request.args.get('message')
        return render_template('admin_estilistas.html', estilistas=lista_estilistas,message=message)

@app.route('/admin/añadir_estilista', methods=['GET', 'POST'])
def añadir_estilista():
    if 'admin' not in session or session['admin']['rol'] != 'admin':
        return redirect(url_for('admin_login'))
    else:
        if request.method == 'POST':
            # Obtener los datos del formulario
            nombre = request.form['nombre']
            telefono = request.form['telefono']
            correo = request.form['correo']
            contrasena = request.form['contrasena']
            activo = int(request.form['activo'])  # Convertir a entero
            foto = request.files['foto']  # Obtenemos el archivo de la foto
            rol = request.form['rol']  # Aquí corregimos el acceso al campo 'rol'
            
            # Guardar la foto en una carpeta (por ejemplo, dentro de 'static/img')
            if foto:
                foto_filename = secure_filename(foto.filename)
                foto.save(os.path.join('static/img', foto_filename))
                foto_url = f'/static/img/{foto_filename}'
            else:
                foto_url = None
            
            # Obtener el siguiente ID numérico
            total_estilistas = app.db.estilistas.count_documents({})
            nuevo_id = total_estilistas + 1  # Establecemos el nuevo ID
            
            # Crear el objeto estilista para guardar en MongoDB
            estilista = {
                'id': nuevo_id,  # Agregamos el nuevo ID
                'nombre': nombre,
                'telefono': telefono,
                'correo': correo,
                'activo': activo,
                'foto_url': foto_url,
                'created_at': datetime.now().strftime('%d-%m-%Y %H:%M'),
                'updated_at': datetime.now().strftime('%d-%m-%Y %H:%M')
            }
            
            estilista_admin = {
                '_id': nuevo_id,
                'idestilista': nuevo_id,
                'pass': contrasena,
                'rol': rol,  # Aquí también corregimos el uso de 'rol'
                'correo': correo
            }
            
            # Guardar en la base de datos
            app.db.estilistas.insert_one(estilista)
            app.db.admin.insert_one(estilista_admin)
            
            # Redirigir al listado de estilistas o a una página de confirmación
            return redirect(url_for('admin_estilistas'))

        # Si es una solicitud GET, mostramos el formulario
        return render_template('agregar_estilista.html')



@app.route('/admin/modificar_estilista/<int:id>', methods=['GET', 'POST'])
def modificar_estilista(id):
    if 'admin' not in session or session['admin']['rol'] != 'admin':
        return redirect(url_for('admin_login'))
    else:
        estilista = app.db.estilistas.find_one({'id': id})  # Obtiene el estilista de la base de datos
        
        if request.method == 'POST':
            nombre = request.form['nombre']
            telefono = request.form['telefono']
            correo = request.form['correo']
            contrasena = request.form['contrasena']
            activo = request.form['activo']
            rol = request.form['rol']
            # Manejo de la foto si se sube una nueva
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto.filename != '':
                    # Aquí guardas la nueva foto (por ejemplo, en una ruta específica)
                    foto.save(os.path.join('static/img/estilistas', foto.filename))
                    # Actualiza la ruta de la foto en la base de datos si es necesario

            # Actualiza los datos del estilista en la base de datos
            app.db.estilistas.update_one({'id': id}, {'$set': {
                'nombre': nombre,
                'telefono': telefono,
                'correo': correo,
                'pass': contrasena,
                'rol': rol,
                'activo': int(activo),
                # 'foto_url': 'ruta/de/la/nueva/foto' si se cambia la foto
            }})

            return redirect(url_for('admin_estilistas'))

        return render_template('admin_modificar_estilista.html', estilista=estilista)


@app.route('/admin/eliminar_estilista/<id>', methods=['POST'])
def eliminar_estilista(id):
    if 'admin' not in session or session['admin']['rol'] != 'admin':
        return redirect(url_for('admin_login'))
    else:
        # Buscar el estilista en la colección 'estilistas' usando su _id
        estilista = app.db.estilistas.find_one({"_id": ObjectId(id)})

        if estilista:
            # Obtener el campo 'id' numérico del estilista
            idestilista = estilista['id']
            
            # Eliminar al estilista en la colección 'admin' usando el id numérico
            resultado_admin = app.db.admin.delete_one({"idestilista": idestilista})

            # Eliminar al estilista en la colección 'estilistas' usando el ObjectId
            resultado_estilista = app.db.estilistas.delete_one({"_id": ObjectId(id)})

            if resultado_estilista.deleted_count > 0:
                message='Estilista eliminado con éxito.'
            else:
                message='No se encontró ningún estilista con ese ID.'

        else:
            message='No se encontró ningún estilista con ese ID.'

        return redirect(url_for('admin_estilistas',message=message))
    
#------------------------------------------------
# ADMIN_RESERVAS
#------------------------------------------------

@app.route('/admin/reservas', methods=['GET', 'POST'])
def admin_reservas():
    if 'admin' not in session or session['admin']['rol'] != 'admin':
        return redirect(url_for('admin_login'))
    else:
        # Obtener todos los estilistas
        estilistas = list(app.db.estilistas.find())
        fechas_ocupadas=obtener_todas_fechas_ocupadas()
        
        return render_template(
            'admin_reservas.html',
            reserva=None,
            estilista=estilistas,
            fechas_ocupadas=fechas_ocupadas
        )


@app.route('/admin/actualizar_fechas',methods=['GET'])
def actualizar_fechas():
    estilista_id=request.args.get('estilista_id')
    if estilista_id:
        fechas_ocupadas=obtener_fechas_ocupadas(estilista_id)
    else:
        fechas_ocupadas=obtener_todas_fechas_ocupadas()
    return jsonify(fechas_ocupadas)

@app.route('/admin/lista_reservas', methods=['GET', 'POST'])
def lista_reservas():
    estilista_id = request.args.get('estilista_id')

    if request.method == 'POST':
        estilista_id = request.form.get('estilista_id')
        
        fechas_ocupadas = obtener_fechas_ocupadas(estilista_id)
        fecha = request.form.get('fecha')
        estilistas = list(app.db.estilistas.find())
        fecha_seleccionada = request.form.get('fecha')
        if not fecha or not estilista_id:
            return render_template('admin_reservas.html', reserva=None, fechas_ocupadas=fechas_ocupadas,estilista=estilistas)
        # Consultar citas del estilista en la fecha seleccionada
        reservas = app.db.cita.find({
            'idestilista': int(estilista_id),
            'fecha': fecha
        })  # 
        lista_reservas = list(reservas)  # Convertir cursor a lista
        lista_reservas.sort(key=lambda x: (x['fecha'], x['hora_inicio']))

        # Obtener información de clientes y estilistas asociada
        reservas_con_info = []
        for reserva in lista_reservas:
            cliente_info = app.db.clientes.find_one({"id": reserva['cliente_id']})
            estilista_info = app.db.estilistas.find_one({"id": reserva['idestilista']})
            
            if cliente_info:
                reserva['cliente'] = cliente_info
            if estilista_info:
                reserva['estilista'] = estilista_info
            reservas_con_info.append(reserva)

        return render_template(
            'admin_reservas.html',
            reserva=reservas_con_info,
            estilista=estilistas,
            fecha_seleccionada=fecha_seleccionada,
            fechas_ocupadas=fechas_ocupadas
        )

    estilistas = list(app.db.estilistas.find())
    
    return render_template('admin_reservas.html', reserva=None, estilista=estilistas)



#------------------------------------------------
# ESTILISTA_RESERVA
#------------------------------------------------
#Estilista

@app.route('/estilista_reservas', methods=['GET'])
def reservas():
    estilista_id = session.get('estilista', {}).get('idestilista')
    fechas_ocupadas = obtener_fechas_ocupadas(estilista_id)  # Obtener fechas ocupadas 
    return render_template('estilista_reservas.html', reserva=None, fechas_ocupadas=fechas_ocupadas)

@app.route('/estilista/lista_reservas', methods=['GET', 'POST'])
def lista_reservas_estilista():
    message = request.args.get('message')
    if request.method == 'POST':
        fecha_seleccionada = request.form.get('fecha')
        estilista_id = session.get('estilista', {}).get('idestilista')
        fechas_ocupadas = obtener_fechas_ocupadas(estilista_id)  # Obtener fechas ocupadas
        if not fecha_seleccionada or not estilista_id:
            return render_template('estilista_reservas.html', reserva=None, fechas_ocupadas=fechas_ocupadas)
        # Obtener las reservas para el estilista y la fecha seleccionada
        reservas = app.db.cita.find({
            'idestilista': estilista_id,
            'fecha': fecha_seleccionada
        })
        # Convertir reservas a lista
        lista_reservas = list(reservas)
        # Serializar reservas (incluyendo información del cliente)
        for reserva in lista_reservas:
            cliente_info = app.db.clientes.find_one({"id": reserva['cliente_id']})
            reserva['cliente'] = cliente_info if cliente_info else {}
        return render_template('estilista_reservas.html', reserva=lista_reservas, fecha_seleccionada=fecha_seleccionada,fechas_ocupadas=fechas_ocupadas)
    return render_template('estilista_reservas.html', reserva=None,message=message)



def obtener_fechas_ocupadas(estilista_id):
    # Filtrar citas por el ID del estilista
    citas = app.db.cita.find({'idestilista': int(estilista_id)})
    fechas_ocupadas = []
    for cita in citas:
        # Convertir la fecha a un objeto datetime si es necesario
        if isinstance(cita['fecha'], str):
            fecha_obj = datetime.strptime(cita['fecha'], '%Y-%m-%d')
        else:
            fecha_obj = cita['fecha']

        # Convertir la fecha al formato requerido y añadirla a la lista
        fechas_ocupadas.append({
            'fecha': fecha_obj.strftime('%Y-%m-%d'),
            'estado': cita.get('estado','Pendiente')
        })

    return fechas_ocupadas


def obtener_todas_fechas_ocupadas():
    
    # Filtrar citas por el ID del estilista
    citas = app.db.cita.find()
    
    fechas_ocupadas = []
    for cita in citas:
        if isinstance(cita['fecha'], str):
            fecha_obj = datetime.strptime(cita['fecha'], '%Y-%m-%d')
        else:
            fecha_obj = cita['fecha']

        # Convertir la fecha al formato requerido y añadirla a la lista
        fechas_ocupadas.append({
            'fecha': fecha_obj.strftime('%Y-%m-%d'),
            'estado': cita.get('estado','Pendiente')
        })

    return fechas_ocupadas



@app.route('/estilista/eliminar_cita/<id>', methods=['POST'])
def eliminar_cita(id):
    if 'estilista' in session and session['estilista']['rol'] == 'estilista':
        print(f"ID de la cita a eliminar: {id}")  # Agrega esta línea para depurar

        # Buscar la cita en la base de datos
        cita = app.db.cita.find_one({"_id": ObjectId(id)})

        if cita:
            # Obtener el ID del cliente
            cliente_id = cita.get('cliente_id')  # Asegúrate de que este campo existe en tu documento

            # Buscar el correo del cliente en la colección de clientes
            cliente = app.db.clientes.find_one({"id": cliente_id})  # Ajusta el campo según tu esquema

            # Extraer el correo del cliente
            correo_cliente = cliente.get('email') if cliente else None

            # Eliminar la cita usando su ObjectId
            resultado_cita = app.db.cita.delete_one({"_id": ObjectId(id)})

            if resultado_cita.deleted_count > 0:
                message='Cita eliminada con éxito.'

                # Enviar correo electrónico de aviso al cliente
                if correo_cliente:
                    enviar_correo_aviso(correo_cliente, cliente.get('nombre'))  # Asegúrate de que el nombre también esté disponible
            else:
                message='No se encontró ninguna cita con ese ID.'
        else:
            message='No se encontró ninguna cita con ese ID.'

        return redirect(url_for('lista_reservas_estilista',message=message))
    elif 'admin' in session and session['admin']['rol'] == 'admin':
        print(f"ID de la cita a eliminar: {id}")  # Agrega esta línea para depurar

        # Buscar la cita en la base de datos
        cita = app.db.cita.find_one({"_id": ObjectId(id)})

        if cita:
            # Obtener el ID del cliente
            cliente_id = cita.get('cliente_id')  # Asegúrate de que este campo existe en tu documento

            # Buscar el correo del cliente en la colección de clientes
            cliente = app.db.clientes.find_one({"id": cliente_id})  # Ajusta el campo según tu esquema

            # Extraer el correo del cliente
            correo_cliente = cliente.get('email') if cliente else None

            # Eliminar la cita usando su ObjectId
            resultado_cita = app.db.cita.delete_one({"_id": ObjectId(id)})

            if resultado_cita.deleted_count > 0:
                message='Cita eliminada con éxito.'

                # Enviar correo electrónico de aviso al cliente
                if correo_cliente:
                    enviar_correo_aviso(correo_cliente, cliente.get('nombre'))  # Asegúrate de que el nombre también esté disponible
            else:
                message='No se encontró ninguna cita con ese ID.'
        else:
            message='No se encontró ninguna cita con ese ID.'

        return redirect(url_for('admin_reservas',message=message))
    else:
            # Redirigir a la página de login si no hay sesión válida
            return redirect(url_for('admin_login'))
    




@app.route('/estilista/finalizar_cita/<id>', methods=['GET'])
def finalizar_cita(id):
    if 'estilista' in session and session['estilista']['rol'] == 'estilista':
            
        # Buscar la cita en la base de datos
        cita = app.db.cita.find_one({"_id": ObjectId(id)})

        if not cita:
            return redirect(url_for('lista_reservas_estilista'))

        # Obtener el ID del cliente
        cliente_id = cita.get('cliente_id')
        idestilista = cita.get('idestilista')

        if not cliente_id:
            return redirect(url_for('lista_reservas_estilista'))

        # Obtener la información del cliente
        cliente_info = app.db.clientes.find_one({"id": cliente_id})

        # Obtener la información del cliente
        estilista_info = app.db.estilistas.find_one({"id": idestilista})    

        # Obtener información adicional de la cita, como servicio, fecha, horas, etc.
        servicio = cita.get('servicio', 'No disponible')
        fecha = cita.get('fecha', 'No disponible')
        hora_inicio = cita.get('hora_inicio', 'No disponible')
        hora_final = cita.get('hora_final', 'No disponible')

        # Redirigir al HTML `finalizar_cita.html` con los datos necesarios
        return render_template('finalizar_cita.html',
                            reserva=cita, 
                            cita_id=id, 
                            cliente_id=cliente_id, 
                            cliente_info=cliente_info,
                            estilista_info=estilista_info, 
                            servicio=servicio, 
                            fecha=fecha, 
                            hora_inicio=hora_inicio, 
                            hora_final=hora_final)
    elif 'admin' in session and session['admin']['rol'] == 'admin':

        # Buscar la cita en la base de datos
        cita = app.db.cita.find_one({"_id": ObjectId(id)})

        if not cita:
            return redirect(url_for('lista_reservas'))

        # Obtener el ID del cliente
        cliente_id = cita.get('cliente_id')
        idestilista = cita.get('idestilista')

        if not cliente_id:
            return redirect(url_for('lista_reservas'))

        # Obtener la información del cliente
        cliente_info = app.db.clientes.find_one({"id": cliente_id})

        # Obtener la información del cliente
        estilista_info = app.db.estilistas.find_one({"id": idestilista})    

        # Obtener información adicional de la cita, como servicio, fecha, horas, etc.
        servicio = cita.get('servicio', 'No disponible')
        fecha = cita.get('fecha', 'No disponible')
        hora_inicio = cita.get('hora_inicio', 'No disponible')
        hora_final = cita.get('hora_final', 'No disponible')

        # Redirigir al HTML `finalizar_cita.html` con los datos necesarios
        return render_template('finalizar_cita.html',
                            reserva=cita, 
                            cita_id=id, 
                            cliente_id=cliente_id, 
                            cliente_info=cliente_info,
                            estilista_info=estilista_info, 
                            servicio=servicio, 
                            fecha=fecha, 
                            hora_inicio=hora_inicio, 
                            hora_final=hora_final)
    else:
            # Redirigir a la página de login si no hay sesión válida
            return redirect(url_for('admin_login'))
   



import os
from werkzeug.utils import secure_filename
from flask import request, flash, redirect, url_for

UPLOAD_FOLDER = './static/resultados'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Configuración para la subida de archivos
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS





@app.route('/finalizar', methods=['GET', 'POST'])
def finalizar():
    if request.method == 'POST':
        try:
            # Captura de los datos del formulario
            nombre = request.form['nombre']
            correo = request.form['correo']
            nombreEstilista = request.form['nombreEstilista']
            idcita = request.form['idcita']
            print(f"ID Cita: {idcita}")  # Para depuración
            idestilista = request.form['idestilista']
            servicio = request.form['servicio']
            fecha = request.form['fecha']
            hora_inicio = request.form['hora_inicio']
            hora_final = request.form['hora_final']
            cliente_id = request.form['cliente_id']
            valor = request.form['valor']
            foto = request.files['foto']
            
            # Imprimir todos los valores para verificar
            print(f"idestilista: {idestilista}, servicio: {servicio}, fecha: {fecha}, hora_inicio: {hora_inicio}, hora_final: {hora_final}, cliente_id: {cliente_id}, valor: {valor}")

            # Manejar la carga de la imagen
            if 'foto' not in request.files:
                message='No se ha seleccionado ninguna imagen.'
                return redirect(request.url)
            
            foto = request.files['foto']
            
            if foto.filename == '':
                message='No se ha seleccionado ninguna imagen.'
                return redirect(request.url)

            # Guardar la imagen en el servidor
            foto.save(os.path.join('static/img/resultados', foto.filename))
            img_url = f"/static/img/resultados/{foto.filename}"
        
            # Verifica que todos los valores estén correctamente capturados antes de guardar
            cita_finalizada = {
                "nombre": nombre,
                "correo": correo,
                "Nombre Estilista": nombreEstilista,
                "id_cita": idcita,
                "id_estilista": idestilista,
                "servicio": servicio,
                "fecha": fecha,
                "hora_inicio": hora_inicio,
                "hora_final": hora_final,
                "id_cliente": cliente_id,
                "monto_final": float(valor),
                "foto_resultado": img_url,
            }
            
            # Imprimir para verificar los datos que se guardarán
            print(f"Cita finalizada a guardar: {cita_finalizada}")

            app.db.cita_finalizada.insert_one(cita_finalizada)
            message='Cita finalizada y guardada exitosamente.'
            # Actualizar el estado de la cita original en la colección cita
            result = app.db.cita.update_one(
                {"idcita": ObjectId(idcita)},  # Filtrar por el ID de la cita
                {"$set": {"estado": "Finalizada"}}  # Actualizar el estado
            )

            # Verificar si la actualización fue exitosa
            if result.modified_count > 0:
                print('Cita finalizada y guardada exitosamente.', 'success')
            else:
                print('Error al actualizar el estado de la cita.', 'error')
            if 'estilista' in session and session['estilista']['rol'] == 'estilista':
                return redirect(url_for('reservas',message=message))
            elif 'admin' in session and session['admin']['rol'] == 'admin':
                return redirect(url_for('admin_reservas',message=message))
            else:
                # Redirigir a la página de login si no hay sesión válida
                return redirect(url_for('admin_login'))
            
            
        except Exception as e:
            return redirect(request.url)
    
    # Si el método es GET, obtén la reserva desde la base de datos
    idcita = request.args.get('idcita')
    if 'estilista' in session and session['estilista']['rol'] == 'estilista':
        # Asumiendo que el id de la cita se pasa como parámetro
        if idcita is None:
            return redirect(url_for('reservas'))
        try:
            # Intenta convertir idcita a un entero
            idcita = int(idcita)
        except ValueError:
            return redirect(url_for('reservas'))
        # Buscar la reserva en la base de datos
        reserva = app.db.reservas.find_one({"id": idcita})
        if not reserva:
            return redirect(url_for('reservas'))

        # Renderizar el formulario y pasar 'reserva' al template
        return render_template('finalizar_cita.html', reserva=reserva)
    elif 'admin' in session and session['admin']['rol'] == 'admin':
        # Asumiendo que el id de la cita se pasa como parámetro
        if idcita is None:
            return redirect(url_for('admin_reservas'))
        try:
            # Intenta convertir idcita a un entero
            idcita = int(idcita)
        except ValueError:
            return redirect(url_for('admin_reservas'))
        # Buscar la reserva en la base de datos
        reserva = app.db.reservas.find_one({"id": idcita})
        if not reserva:
            return redirect(url_for('admin_reservas'))

        # Renderizar el formulario y pasar 'reserva' al template
        return render_template('finalizar_cita.html', reserva=reserva)
    else:
        # Redirigir a la página de login si no hay sesión válida
        return redirect(url_for('admin_login'))
    



#------------------------------------------------
# ESTILISTA_DISPONIBILIDAD
#------------------------------------------------

#notocar
@app.route('/estilista/crear_disponibilidad', methods=['GET', 'POST'])
def crear_disponibilidad():
    if 'estilista' not in session or session['estilista']['rol'] != 'estilista':
        return redirect(url_for('admin_login'))
    else:
        return render_template('generar_disponibilidad.html')
        

@app.route('/estilista/crear_disponibilidad', methods=['GET', 'POST'])
def crear_disponibilidad_estilista():
    if 'estilista' not in session or session['admin']['rol'] != 'estilista':
        return redirect(url_for('admin_login'))
    else:
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
            return redirect(url_for('crear_disponibilidad'))

        return render_template('estilista_crear_disponibilidad.html')
    




#------------------------------------------------
# PORTAFOLIO
#------------------------------------------------
@app.route('/portafolio')
def portafolio():
    # Consultar los datos desde la base de datos
    citas = list(app.db.cita_finalizada.find({}, {
        "foto_resultado": 1,
        "Nombre Estilista": 1,
        "nombre": 1,
        "fecha": 1,
        "_id": 0,
        "servicio":1,
        "hora_inicio":1,
        "hora_final":1
    }))

    return render_template('portafolio.html', citas=citas)

    

#------------------------------------------------
# DATOS DE NEGOCIO
#------------------------------------------------


@app.route('/admin/datos_negocio')
def datos_negocio():
    # Mapeo de meses
    meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    # Citas por estilista
    estilistas = list(app.db.estilistas.find({}, {"id": 1, "nombre": 1}))
    citas_por_estilista = app.db.cita.aggregate([
        {"$group": {"_id": "$idestilista", "citas": {"$sum": 1}}}
    ])
    estilistas_data = [
        {
            "nombre": next((e["nombre"] for e in estilistas if e["id"] == data["_id"]), "Desconocido"),
            "citas": data["citas"]
        }
        for data in citas_por_estilista
    ]
    
    # Clientes con más citas
    top_clientes = app.db.cita.aggregate([
        {"$group": {"_id": "$cliente_id", "cantidad": {"$sum": 1}}},
        {"$sort": {"cantidad": -1}},
        {"$limit": 5}
    ])
    clientes = {cliente["id"]: cliente["nombre"] for cliente in app.db.clientes.find({}, {"id": 1, "nombre": 1})}
    top_clientes_data = [
        {
            "cliente_id": cliente["_id"],
            "cantidad": cliente["cantidad"],
            "nombre_cliente": clientes.get(cliente["_id"], "Desconocido")
        }
        for cliente in top_clientes
    ]
    
    # Servicios más requeridos
    servicios_requeridos = app.db.cita.aggregate([
        {"$group": {"_id": "$servicio", "cantidad": {"$sum": 1}}},
        {"$sort": {"cantidad": -1}},
        {"$limit": 5}
    ])
    servicios = {servicio["nombre"].lower(): servicio["nombre"] for servicio in app.db.servicios.find({}, {"nombre": 1})}
    servicios_data = [
        {
            "nombre_servicio": servicios.get(servicio["_id"].lower(), "Desconocido"),
            "cantidad": servicio["cantidad"]
        }
        for servicio in servicios_requeridos
    ]

    # Montos finales por estilista y por mes
    montos_por_estilista_por_mes = list(app.db.cita_finalizada.aggregate([
        {
            "$addFields": {
                "mes": {"$month": {"$toDate": "$fecha"}}
            }
        },
        {
            "$group": {
                "_id": {"estilista": "$Nombre Estilista", "mes": "$mes"},
                "monto_total": {"$sum": "$monto_final"}
            }
        },
        {"$sort": {"_id.estilista": 1, "_id.mes": 1}}
    ]))
    # Reemplazar números de mes por nombres
    for item in montos_por_estilista_por_mes:
        item["_id"]["mes"] = meses[item["_id"]["mes"]]

    # Montos finales por mes
    montos_por_mes = list(app.db.cita_finalizada.aggregate([
        {
            "$addFields": {
                "mes": {"$month": {"$toDate": "$fecha"}}
            }
        },
        {
            "$group": {
                "_id": "$mes",
                "monto_total": {"$sum": "$monto_final"}
            }
        },
        {"$sort": {"_id": 1}}
    ]))
    # Reemplazar números de mes por nombres
    for item in montos_por_mes:
        item["_id"] = meses[item["_id"]]

    # Realizar la agregación para sumar todos los "monto_final"
    suma_montos = app.db.cita_finalizada.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$monto_final"}}}
    ])
    resultado = next(suma_montos, {"total": 0})
    total_monto_final = resultado["total"]

    return render_template(
        'datos_negocio.html',
        estilistas_data=estilistas_data,
        top_clientes_data=top_clientes_data,
        servicios_data=servicios_data,
        total_monto_final=total_monto_final,
        montos_por_estilista_por_mes=montos_por_estilista_por_mes,
        montos_por_mes=montos_por_mes
    )



if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=os.getenv("PORT", default=5000))
