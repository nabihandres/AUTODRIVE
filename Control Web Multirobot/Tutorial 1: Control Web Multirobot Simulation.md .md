# Sistema de Monitoreo y Control Web de Robots Móviles en Entornos Industriales

Este proyecto implementa un sistema virtual para la simulación, navegación, monitoreo y control de múltiples robots móviles autónomos en un entorno industrial.

# 1. Requisitos del sistema

## 1.1 Requisitos del Software

### Sistema operativo

* Ubuntu 22.04 LTS.
* Arquitectura de 64 bits.
* ROS 2 Humble Hawksbill.

Gazebo, Nav2, RViz y los paquetes TurtleBot3 utilizados por este proyecto están orientados a ROS 2 Humble sobre Ubuntu 22.04.

### Librerías y software necesario

* Git.
* Python 3.
* ROS 2 Humble.
* Colcon.
* rosdep.
* Gazebo Classic.
* Navigation2 (Nav2).
* TurtleBot3.
* rosbridge_server.
* web_video_server.
* RViz 2.

## 1.2 Requisitos de Hardware

Para la implementación completa del sistema se requieren cuatro robots móviles autónomos. Cada robot debe contar con:

* Una computadora embebida tipo Raspberry Pi (o equivalente).
* Sistema operativo Ubuntu 22.04 instalado.
* ROS 2 Humble correctamente configurado.
* Todas las dependencias del proyecto instaladas (Nav2, rosbridge, sensores, etc.).
* Sensores Lidar para percepción del entorno y navegación.
* Conectividad de red para comunicación con el sistema central.

---

## Índice
1. [Requisitos del sistema](#1-requisitos-del-sistema)
   * [1.1 Requisitos del software](#11-requisitos-del-software)
   * [1.2 Requisitos de hardware](#12-requisitos-de-hardware)

2. [Resumen y comandos de ejecución](#2-resumen-y-comandos-de-ejecución)

3. [Clonación del repositorio](#3-clonación-del-repositorio)

   * [3.1 Clonación de modelos industriales para Gazebo](#31-clonación-de-modelos-industriales-para-gazebo)
   * [3.2 Eliminar resultados de compilaciones anteriores](#32-eliminar-resultados-de-compilaciones-anteriores)

4. [Arquitectura y ejecución de la simulación](#4-arquitectura-y-ejecución-de-la-simulación)

   * [4.1 Launch file principal de la simulación](#41-launch-file-principal-de-la-simulación)
   * [4.2 Directorio `amr/amr`](#42-directorio-amramr)
   * [4.3 Simulación multirrobot y navegación](#43-simulación-multirrobot-y-navegación)
   * [4.4 Interfaz web de monitoreo y control](#44-interfaz-web-de-monitoreo-y-control)


---

# 2. Resumen y comandos de ejecución

Esta sección reúne únicamente los comandos necesarios para compilar y ejecutar el proyecto.
Los comandos deben ejecutarse en el orden indicado.

### 1. Entrar al workspace

```bash
cd ~/Monitoreo_Control_Web_Multirobot
```

### 2. Cargar ROS 2 Humble

```bash
source /opt/ros/humble/setup.bash
```

### 3. Limpiar compilaciones anteriores

Este paso se recomienda durante la primera instalación o después de realizar cambios importantes en los paquetes:

```bash
rm -rf build install log
```

> [!WARNING]
> No se debe escribir `/build`, `/install` o `/log`, ya que la `/` inicial hace referencia a la raíz del sistema operativo.

### 4. Compilar el proyecto

```bash
colcon build --symlink-install
```

### 5. Cargar el workspace compilado

```bash
source install/setup.bash
```

### 6. Iniciar la simulación

En la **Terminal 1**, ejecutar:

```bash
cd ~/Monitoreo_Control_Web_Multirobot

source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch amr multi_amr_project_launch.launch.py
```

### 7. Consultar la dirección IP del equipo

En una nueva terminal, ejecutar:

```bash
hostname -I
```

> [!IMPORTANT]
>
> # 🚨 CONFIGURACIÓN OBLIGATORIA
>
> Antes de utilizar la página web, se debe reemplazar la dirección IP existente en el archivo JavaScript por la IP de la computadora que ejecuta ROS 2.
>
> Se debe modificar:
>
> * La conexión WebSocket del puerto `9090`.
> * La cámara de `amr_0` en el puerto `8080`.
> * La cámara de `amr_1` en el puerto `8081`.
> * La cámara de `amr_2` en el puerto `8082`.
> * La cámara de `amr_3` en el puerto `8083`.
>
> Si la IP no se actualiza, la interfaz web no podrá comunicarse correctamente con el proyecto.

La conexión WebSocket debe tener una estructura similar a:

```javascript
var ros = new ROSLIB.Ros({
    url: 'ws://192.168.1.50:9090'
});
```

Las direcciones de video deben utilizar la misma IP:

```javascript
const videoURL =
    `http://192.168.1.50:8080/stream?topic=${videoTopic}`;
```

Para los demás robots se utilizan los puertos `8081`, `8082` y `8083`.

### 8. Iniciar la interfaz web

Se recomienda abrir el proyecto en Visual Studio Code:

```bash
cd ~/Monitoreo_Control_Web_Multirobot
code .
```

Después:

1. Abrir `web/index.html`.
2. Hacer clic derecho sobre el archivo.
3. Seleccionar **Open with Live Server**.

La interfaz se abrirá normalmente en:

```text
http://127.0.0.1:5500/web/index.html
```

Como alternativa, en la **Terminal 2** puede utilizarse el servidor HTTP de Python:

```bash
cd ~/Monitoreo_Control_Web_Multirobot/web

python3 -m http.server
```

Abrir en el navegador:

```text
http://localhost:8000
```

Para acceder desde otra computadora de la misma red:

```text
http://IP_DEL_EQUIPO_ROS:8000
```

Por ejemplo:

```text
http://192.168.1.50:8000
```

> [!NOTE]
> Cuando se utilice Live Server, no es necesario ejecutar `python3 -m http.server`. Ambos métodos cumplen la misma función de servir los archivos de la interfaz web.

---
# 3. Clonación del repositorio

Ubicarse en el directorio personal:

```bash
cd ~
```

Clonar el repositorio principal del proyecto:

```bash
git clone https://github.com/lfvargas20/Monitoreo_Control_Web_Multirobot.git
```

Entrar al workspace:

```bash
cd ~/Monitoreo_Control_Web_Multirobot
```

> **Importante:** Linux distingue entre letras mayúsculas y minúsculas. Debe utilizarse exactamente `Monitoreo_Control_Web_Multirobot`.

## 3.1 Clonación de modelos industriales para Gazebo

El proyecto utiliza modelos industriales adicionales para la simulación en Gazebo. Estos modelos deben descargarse manualmente y configurarse para que Gazebo pueda encontrarlos.

Crear un directorio para almacenar los modelos:

```bash
mkdir -p ~/gazebo_models
cd ~/gazebo_models
```

Clonar el repositorio de modelos industriales:

```bash
git clone https://github.com/osrf/gazebo_models.git
```

Una vez descargados, es necesario indicarle a Gazebo dónde se encuentran estos modelos. Para ello, se debe configurar la variable de entorno `GAZEBO_MODEL_PATH`.

Agregar la ruta al archivo `~/.bashrc`:

```bash
echo "export GAZEBO_MODEL_PATH=\$GAZEBO_MODEL_PATH:~/gazebo_models/gazebo_models" >> ~/.bashrc
source ~/.bashrc
```

Verificar que la variable se haya configurado correctamente:

```bash
echo $GAZEBO_MODEL_PATH
```

La salida debe incluir la ruta:

```text
~/gazebo_models/gazebo_models
```

Con esto, Gazebo podrá localizar automáticamente los modelos industriales descargados al momento de ejecutar las simulaciones.

## 3.2 Eliminar resultados de compilaciones anteriores

El repositorio contiene carpetas `build`, `install` y `log` generadas en otra computadora. Es recomendable eliminarlas antes de compilar.

```bash
rm -rf build install log
```

No se debe utilizar:

```bash
rm -rf /build /install /log
```

La `/` inicial representa la raíz del sistema operativo y no el directorio del proyecto.

---

# 4. Arquitectura y ejecución de la simulación

El paquete `amr` constituye el punto principal de entrada del proyecto. En él se encuentran los archivos necesarios para describir los robots, configurar su navegación, cargar el entorno industrial, iniciar la simulación multirrobot y conectar ROS 2 con la interfaz web.

Su estructura general es la siguiente:

```text
src/amr/
├── amr/
│   ├── __init__.py
│   ├── node_trigger_goal_1.py
│   ├── node_trigger_goal_2.py
│   ├── node_trigger_goal_3.py
│   ├── node_trigger_goal_4.py
│   ├── node_trigger_goal_tb3_1.py
│   ├── node_trigger_goal_tb3_2.py
│   ├── node_trigger_goal_tb3_3.py
│   └── node_trigger_goal_tb3_4.py
├── launch/
├── map/
├── models/
├── param/
├── resource/
├── urdf/
├── worlds/
├── package.xml
├── setup.cfg
└── setup.py
```

Las carpetas principales cumplen las siguientes funciones:

| Directorio | Función                                                                      |
| ---------- | ---------------------------------------------------------------------------- |
| `amr/`     | Contiene los nodos Python ejecutables del paquete.                           |
| `launch/`  | Contiene los launch files que inician la simulación y los nodos del sistema. |
| `map/`     | Almacena el mapa de ocupación utilizado por Nav2.                            |
| `models/`  | Contiene modelos y mallas tridimensionales de los robots.                    |
| `param/`   | Contiene los archivos YAML con los parámetros de navegación de cada robot.   |
| `urdf/`    | Contiene la descripción física, visual y cinemática de los robots.           |
| `worlds/`  | Contiene el mundo industrial que se carga en Gazebo Classic.                 |

---

## 4.1 Launch file principal de la simulación

El archivo principal utilizado para iniciar el proyecto es:

```text
src/amr/launch/multi_amr_project_launch.launch.py
```

Este launch file funciona como el **punto de entrada general del sistema**. Su función es agrupar e iniciar los componentes principales de la simulación mediante un solo comando.

El archivo puede dividirse en cuatro bloques principales.

### Localización de los archivos del paquete

La función:

```python
get_package_share_directory('amr')
```

obtiene la ruta en la que ROS 2 instaló los recursos del paquete `amr`.

Esto permite localizar los launch files sin utilizar rutas absolutas vinculadas a una computadora específica.

### Inicio de la simulación multirrobot

El primer bloque incluye:

```text
nav2_multirobot_launch.launch.py
```

Este archivo secundario se encarga de iniciar la simulación multirrobot y los componentes de navegación asociados.

```python
gazebo_nav2_multirobot = IncludeLaunchDescription(...)
```

El launch principal no configura directamente cada robot, sino que delega esa tarea al archivo incluido.

### Inicio de los nodos de envío de objetivos

El segundo bloque incluye:

```text
node_trigger_multirobot_launch.launch.py
```

Este archivo inicia los nodos:

```text
node_trigger_goal_1
node_trigger_goal_2
node_trigger_goal_3
node_trigger_goal_4
```

Estos nodos reciben las posiciones objetivo enviadas desde la interfaz web y las transmiten al sistema Nav2 de cada robot.

### Comunicación con la interfaz web

El nodo:

```text
rosbridge_websocket_1
```

pertenece al paquete `rosbridge_server` y abre una conexión WebSocket en el puerto:

```text
9090
```

Esta conexión permite que la aplicación desarrollada en JavaScript pueda publicar y recibir mensajes de ROS 2.

El flujo general es:

```text
Interfaz web
     │
     │ WebSocket: puerto 9090
     ▼
rosbridge_server
     │
     ▼
Topics y acciones de ROS 2
```

### Servidores de video

El launch inicia cuatro instancias de `web_video_server`:

| Nodo                 | Puerto |
| -------------------- | -----: |
| `web_video_server_1` | `8080` |
| `web_video_server_2` | `8081` |
| `web_video_server_3` | `8082` |
| `web_video_server_4` | `8083` |

Estos servidores permiten visualizar desde el navegador las imágenes publicadas en topics de ROS 2.

Cada servidor utiliza los siguientes parámetros de comunicación:

```text
reliability: reliable
history: keep_last
depth: 10
```

Estos parámetros indican que se utiliza una comunicación confiable y que se conservan únicamente los diez mensajes más recientes en la cola.

### Descripción final del lanzamiento

Finalmente, todos los componentes se agregan a un objeto `LaunchDescription`:

```python
return LaunchDescription([
    gazebo_nav2_multirobot,
    gazebo_nav2_multirobot_trigger,
    rosbridge_websocket_1,
    web_video_server_1,
    web_video_server_2,
    web_video_server_3,
    web_video_server_4
])
```

En términos generales, el launch principal inicia:

```text
multi_amr_project_launch.launch.py
├── Simulación multirrobot y navegación
├── Nodos para enviar objetivos a Nav2
├── rosbridge_server en el puerto 9090
└── Servidores de video en los puertos 8080–8083
```

De esta manera, el proyecto puede iniciarse mediante un único comando:

```bash
ros2 launch amr multi_amr_project_launch.launch.py
```

> **Nota:** este launch file actúa principalmente como coordinador. La configuración detallada de Gazebo, los robots y Nav2 se encuentra en `nav2_multirobot_launch.launch.py`, mientras que la creación de los nodos para enviar objetivos se encuentra en `node_trigger_multirobot_launch.launch.py`.

---

## 4.2 Directorio `amr/amr`

El directorio:

```text
src/amr/amr/
```

contiene los nodos Python que conectan la interfaz web con el sistema de navegación Nav2.

Para los robots AMR se incluyen los siguientes nodos:

```text
node_trigger_goal_1.py
node_trigger_goal_2.py
node_trigger_goal_3.py
node_trigger_goal_4.py
```

Cada nodo controla el envío de objetivos para un robot diferente:

| Nodo                  | Robot   |
| --------------------- | ------- |
| `node_trigger_goal_1` | `amr_0` |
| `node_trigger_goal_2` | `amr_1` |
| `node_trigger_goal_3` | `amr_2` |
| `node_trigger_goal_4` | `amr_3` |

Por ejemplo, `node_trigger_goal_1.py` se comunica con el sistema de navegación del robot `amr_0`.

El nodo recibe desde la interfaz web:

| Topic                     | Tipo              | Función                           |
| ------------------------- | ----------------- | --------------------------------- |
| `/amr_0/pose_x`           | `std_msgs/String` | Coordenada X del objetivo.        |
| `/amr_0/pose_y`           | `std_msgs/String` | Coordenada Y del objetivo.        |
| `/amr_0/pose_yaw`         | `std_msgs/String` | Orientación objetivo en radianes. |
| `/amr_0/start_navigation` | `std_msgs/Bool`   | Orden para iniciar la navegación. |

Cuando recibe la orden de inicio, el nodo construye una meta de tipo:

```text
nav2_msgs/action/NavigateToPose
```

La posición se expresa con respecto al frame global:

```text
map
```

El ángulo `yaw` se convierte en un cuaternión antes de asignarlo a la orientación del robot. Posteriormente, la meta se envía al servidor de acciones de Nav2:

```text
/amr_0/navigate_to_pose
```

Cuando la navegación termina o la meta es rechazada, el nodo publica el resultado en:

```text
/amr_0/navigation_status
```

Los principales resultados que puede publicar son:

```text
SUCCEEDED
CANCELED
ABORTED
REJECTED
UNKNOWN
```

El feedback recibido durante el desplazamiento se muestra únicamente en la terminal y no se publica en la interfaz web.

El flujo general es:

```text
Interfaz web
     │
     ├── posición X
     ├── posición Y
     ├── orientación yaw
     └── iniciar navegación
              │
              ▼
     node_trigger_goal_1
              │
              ├── construye la meta
              ├── convierte yaw a cuaternión
              └── envía NavigateToPose
                          │
                          ▼
                    Nav2 de amr_0
                          │
                          ▼
             /amr_0/navigation_status
```

Los nodos correspondientes a `amr_1`, `amr_2` y `amr_3` siguen el mismo funcionamiento general, utilizando los topics y acciones pertenecientes a cada namespace.

---

## 4.3 Simulación multirrobot y navegación

El archivo:

```text
src/amr/launch/nav2_multirobot_launch.launch.py
```

se encarga de iniciar Gazebo Classic, cargar el entorno industrial y crear las instancias de simulación y navegación de los cuatro robots.

Este launch file es incluido automáticamente por `multi_amr_project_launch.launch.py`, por lo que normalmente no es necesario ejecutarlo de manera independiente.

### Recursos utilizados

Al inicio, el launch localiza los recursos pertenecientes a los paquetes `amr` y `nova_nav2_bringup`:

```python
bringup_dir = get_package_share_directory('nova_nav2_bringup')
gazebo_dir = get_package_share_directory('amr')
```

A partir de estas rutas obtiene:

* El mundo de Gazebo.
* El mapa de ocupación.
* Los archivos de parámetros de Nav2.
* La configuración de RViz.
* Los launch files auxiliares.

El mundo y el mapa utilizados por defecto son:

```text
src/amr/worlds/factory.world
src/amr/map/factory_map_copy_1.yaml
```

### Robots y posiciones iniciales

El archivo define cuatro robots con nombres y posiciones iniciales diferentes:

| Robot   |  X [m] |  Y [m] | Yaw [rad] |
| ------- | -----: | -----: | --------: |
| `amr_0` |  `0.0` |  `0.0` |    `3.14` |
| `amr_1` |  `0.0` |  `4.0` |     `0.0` |
| `amr_2` | `12.0` |  `4.0` |    `4.71` |
| `amr_3` | `14.0` | `-5.0` |     `0.0` |

Estos valores determinan dónde aparece cada robot al iniciar la simulación.

### Argumentos configurables

El launch declara varios argumentos que permiten modificar la ejecución sin cambiar directamente el código:

* `world`: mundo que se cargará en Gazebo.
* `simulator`: ejecutable utilizado para iniciar Gazebo.
* `map`: mapa utilizado por Nav2.
* `amr_i_params_file`: parámetros de navegación de cada robot.
* `autostart`: inicia automáticamente los nodos de Nav2.
* `rviz_config`: configuración visual de RViz.
* `use_rviz`: determina si se inicia RViz.
* `use_robot_state_pub`: determina si se inicia `robot_state_publisher`.

Cada robot utiliza un archivo de parámetros independiente:

```text
nav2_multirobot_params_1.yaml
nav2_multirobot_params_2.yaml
nav2_multirobot_params_3.yaml
nav2_multirobot_params_4.yaml
```

Esto permite adaptar individualmente sus frames, topics, costmaps y componentes de navegación.

### Inicio de Gazebo

Gazebo Classic se inicia mediante:

```python
ExecuteProcess(...)
```

El comando carga el mundo industrial junto con los plugins:

```text
libgazebo_ros_init.so
libgazebo_ros_factory.so
```

Estos plugins permiten conectar Gazebo con ROS 2 y crear los robots dentro de la simulación.

### Creación de las instancias de navegación

El launch recorre la lista de robots mediante:

```python
for robot in robots:
```

Para cada robot crea un grupo de acciones independiente.

Primero inicia RViz con el namespace correspondiente:

```text
amr_0
amr_1
amr_2
amr_3
```

Luego incluye:

```text
amr_simulation_launch.py
```

y le envía la configuración específica del robot:

* Namespace.
* Nombre.
* Posición inicial.
* Orientación inicial.
* Mapa.
* Archivo de parámetros.
* Uso del tiempo de simulación.
* Inicio automático de Nav2.
* Activación de `robot_state_publisher`.

El uso de namespaces evita conflictos entre los topics, nodos, acciones y transformaciones de los diferentes robots.

El funcionamiento general es:

```text
nav2_multirobot_launch.py
├── Inicia Gazebo y factory.world
├── Carga factory_map_copy_1.yaml
├── amr_0 + parámetros 1 + Nav2 + RViz
├── amr_1 + parámetros 2 + Nav2 + RViz
├── amr_2 + parámetros 3 + Nav2 + RViz
└── amr_3 + parámetros 4 + Nav2 + RViz
```

### Mensajes de diagnóstico

El launch también muestra en la terminal información sobre cada robot, como:

* Nombre del robot.
* Mapa utilizado.
* Archivo de parámetros.
* Configuración de RViz.
* Estado de `robot_state_publisher`.
* Estado del inicio automático de Nav2.

Estos mensajes facilitan la comprobación de la configuración durante el arranque.

### Construcción final del lanzamiento

Finalmente, el archivo agrega a `LaunchDescription`:

1. Los argumentos configurables.
2. El proceso de Gazebo.
3. Las cuatro instancias de simulación y navegación.

Este launch file constituye, por tanto, el componente encargado de preparar el entorno compartido y crear una instancia independiente de Nav2 para cada robot.

---
## 4.4 Interfaz web de monitoreo y control

La interfaz web del proyecto se encuentra en:

```text
Monitoreo_Control_Web_Multirobot/web/
```

El archivo principal es:

```text
index.html
```

Este archivo define la estructura visual de la página y carga los archivos CSS y JavaScript utilizados para interactuar con ROS 2.

### Ejecución con Visual Studio Code

Para ejecutar la interfaz se recomienda utilizar la extensión **Live Server** de Visual Studio Code.

Abrir el proyecto:

```bash
cd ~/Monitoreo_Control_Web_Multirobot
code .
```

Dentro de Visual Studio Code:

1. Instalar la extensión **Live Server**.
2. Abrir `web/index.html`.
3. Hacer clic derecho sobre el archivo.
4. Seleccionar **Open with Live Server**.

La página se abrirá normalmente en una dirección similar a:

```text
http://127.0.0.1:5500/web/index.html
```

También puede utilizarse el servidor HTTP de Python:

```bash
cd ~/Monitoreo_Control_Web_Multirobot/web
python3 -m http.server
```

En este caso, la interfaz estará disponible en:

```text
http://localhost:8000
```

> [!IMPORTANT]
> La simulación debe estar ejecutándose antes de utilizar la interfaz web. De lo contrario, la página no podrá conectarse con `rosbridge_server`, los topics de ROS 2 ni los servidores de video.

### Configuración obligatoria de la dirección IP

El archivo JavaScript contiene una dirección IP escrita directamente en el código:

```javascript
var ros = new ROSLIB.Ros({
    url: 'ws://192.168.100.122:9090'
});
```

> [!IMPORTANT]
>
> # 🚨 CAMBIO OBLIGATORIO DE IP
>
> Debe reemplazarse `192.168.100.122` por la dirección IP de la computadora que ejecuta ROS 2 y la simulación.
>
> Si esta dirección no se cambia correctamente, la interfaz web no podrá conectarse con ROS 2 y el proyecto no funcionará desde la página web.

Para conocer la dirección IP del equipo:

```bash
hostname -I
```

Ejemplo de salida:

```text
192.168.1.50
```

La conexión debe modificarse así:

```javascript
var ros = new ROSLIB.Ros({
    url: 'ws://192.168.1.50:9090'
});
```

### Conexión con ROS 2

La interfaz utiliza `ROSLIB.js` para comunicarse con ROS 2 mediante WebSocket.

El código registra tres eventos principales:

* `connection`: la conexión con ROS 2 se estableció correctamente.
* `error`: ocurrió un problema durante la conexión.
* `close`: la conexión con ROS 2 fue cerrada.

Estos mensajes pueden revisarse desde la consola del navegador presionando `F12`.

### Selección del robot

La interfaz permite seleccionar uno de los cuatro robots:

```text
amr_0
amr_1
amr_2
amr_3
```

Las funciones:

```javascript
showRobot1()
showRobot2()
showRobot3()
showRobot4()
```

actualizan los topics y datos mostrados según el robot seleccionado.

Al cambiar de robot, la página:

* selecciona su topic `/cmd_vel`;
* carga su cámara;
* se suscribe a su odometría;
* se suscribe a su escáner láser;
* escucha el resultado de navegación;
* elimina suscripciones que pertenecen a otros robots.

### Control manual

La interfaz publica mensajes de tipo:

```text
geometry_msgs/msg/Twist
```

en los siguientes topics:

```text
/amr_0/cmd_vel
/amr_1/cmd_vel
/amr_2/cmd_vel
/amr_3/cmd_vel
```

Los botones permiten:

* avanzar;
* retroceder;
* girar en sentido horario;
* girar en sentido antihorario;
* detener el robot.

La velocidad lineal cambia en incrementos de:

```text
0.05 m/s
```

La velocidad angular cambia en incrementos de:

```text
0.03 rad/s
```

### Monitoreo de sensores

La interfaz se suscribe a la odometría de cada robot:

```text
/amr_i/odom
```

A partir de estos mensajes muestra:

* velocidad lineal;
* velocidad angular;
* orientación roll;
* orientación pitch;
* orientación yaw.

También se suscribe al escáner láser:

```text
/amr_i/scan
```

La distancia mínima detectada se utiliza para generar una alarma de proximidad cuando un obstáculo se encuentra aproximadamente a menos de:

```text
0.20 m
```

El código también genera una alarma de estabilidad cuando los valores de roll o pitch superan el límite configurado.

### Visualización de las cámaras

Cada robot utiliza un servidor de video diferente:

| Robot   | Topic de cámara           | Puerto |
| ------- | ------------------------- | -----: |
| `amr_0` | `/amr_0/camera/image_raw` | `8080` |
| `amr_1` | `/amr_1/camera/image_raw` | `8081` |
| `amr_2` | `/amr_2/camera/image_raw` | `8082` |
| `amr_3` | `/amr_3/camera/image_raw` | `8083` |

El archivo JavaScript contiene direcciones como:

```javascript
const videoURL =
    `http://192.168.100.122:8080/stream?topic=${videoTopic}`;
```

> [!IMPORTANT]
>
> # 🚨 CAMBIO OBLIGATORIO EN LAS CÁMARAS
>
> La dirección `192.168.100.122` debe reemplazarse por la misma IP configurada en la conexión WebSocket.
>
> Este cambio debe realizarse en las funciones:
>
> ```text
> showRobot1()
> showRobot2()
> showRobot3()
> showRobot4()
> ```
>
> Si no se modifica la IP en estas cuatro direcciones, la interfaz puede conectarse con ROS 2, pero las cámaras no se mostrarán.

### Visualización del mapa

La página se suscribe al mapa mediante:

```text
/amr_0/map
```

El mensaje:

```text
nav_msgs/msg/OccupancyGrid
```

se transforma en una imagen dibujada sobre un elemento HTML `canvas`.

Sobre el mapa se representan:

* las posiciones de los cuatro robots;
* las trayectorias recorridas;
* la posición objetivo seleccionada.

Cada robot utiliza un color diferente para facilitar su identificación.

### Envío de objetivos de navegación

La función:

```javascript
startGoal()
```

lee las coordenadas introducidas por el usuario:

```text
x
y
theta
```

El ángulo `theta`, introducido en grados, se convierte a radianes antes de enviarse.

Según el robot seleccionado, la interfaz publica en:

```text
/amr_i/pose_x
/amr_i/pose_y
/amr_i/pose_yaw
/amr_i/start_navigation
```

Los nodos `node_trigger_goal_*` reciben estos datos y generan una meta `NavigateToPose` para Nav2.

La interfaz escucha el resultado mediante:

```text
/amr_i/navigation_status
```

### Cancelación de objetivos

La función:

```javascript
cancelGoal()
```

utiliza el servicio de cancelación asociado con la acción `NavigateToPose`:

```text
/amr_i/navigate_to_pose/_action/cancel_goal
```

El tipo de servicio utilizado es:

```text
action_msgs/srv/CancelGoal
```

Esto permite solicitar la cancelación de la navegación activa del robot seleccionado.

### Flujo general de la interfaz

```text
Interfaz web
     │
     ├── Control manual → /amr_i/cmd_vel
     ├── Posición objetivo → /amr_i/pose_*
     ├── Inicio de navegación → /amr_i/start_navigation
     ├── Cancelación → NavigateToPose/cancel_goal
     │
     ├── Odometría ← /amr_i/odom
     ├── Láser ← /amr_i/scan
     ├── Estado ← /amr_i/navigation_status
     ├── Mapa ← /amr_0/map
     └── Cámara ← web_video_server
```

> [!IMPORTANT]
>
> # 🚨 RESUMEN OBLIGATORIO
>
> Antes de utilizar la interfaz se debe comprobar que la dirección IP correcta esté configurada en:
>
> 1. La conexión WebSocket de `ROSLIB.Ros`.
> 2. La dirección de video de `amr_0`.
> 3. La dirección de video de `amr_1`.
> 4. La dirección de video de `amr_2`.
> 5. La dirección de video de `amr_3`.
>
> Si cualquiera de estas direcciones conserva una IP perteneciente a otra computadora, esa parte del sistema no funcionará.
