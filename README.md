# 📈 Bellabeat Strategic Segmentation Analysis
(Análisis Estratégico y Segmentación de Clientes para Bellabeat)

## 🎯 Resumen del Proyecto
Este proyecto es un caso de estudio completo de **Data Analytics** realizado para [**Bellabeat**](https://bellabeat.com), una empresa de tecnología enfocada en el bienestar femenino. El objetivo principal es informar la estrategia de crecimiento y marketing de Bellabeat mediante la **segmentación** de los hábitos de actividad y consistencia de los usuarios.

Utilizamos el dataset público de FitBit como un *proxy* representativo para analizar el comportamiento y generar recomendaciones accionables sobre el desarrollo de productos y las campañas de *re-engagement*.

## 🛠️ Habilidades Técnicas Demostradas

Este análisis combina rigurosamente la **Ingeniería de Datos (ETL)** con la **Estadística Descriptiva y el Análisis de Negocio**.

* **Ingeniería de Datos (ETL):** Procesamiento, limpieza y consolidación del dataset FitBit original.
    * **Corrección de Errores Críticos:** Validación y ajuste de las unidades de **tiempo** y los umbrales de **METs** (equivalente metabólico) para garantizar la precisión de las métricas de intensidad.
    * **Feature Engineering:** Creación de variables de alto impacto, como el **Puntaje de Actividad Combinada** (`combined_activity_score`) para medir el esfuerzo efectivo del usuario (Minutos Vigorosos x 2 + Minutos Moderados).
* **Segmentación y Análisis:**
    * **Definición de Benchmarks:** Uso de directrices de la **OMS** y el **JACC** para establecer umbrales de actividad saludable.
    * **Segmentación Avanzada:** Clasificación de clientes en cuadrantes de negocio (e.g., "Sedentario en Riesgo", "Fuerte", "Saludable") mediante el cruce de **Mediana de Pasos** e **Intensidad Típica**.
* **Herramientas:** Python (Pandas, NumPy), Jupyter Notebook, Matplotlib, Seaborn.

## 📊 Hallazgos Clave

1.  **Validación de la Intensidad:** Se confirmó una correlación muy fuerte (r > 0.91) entre el Puntaje de Actividad Combinada y el Gasto Calórico.
2.  **Identificación de Riesgo:** El análisis de volumen reveló que el mayor riesgo de salud se concentra en los segmentos de pasos bajos, con **294 días totales** sin alcanzar el umbral mínimo de salud.
3.  **Tipos de Clientes:** Se identificaron 4 segmentos clave, siendo los **Sedentarios (30.8%)** y los **Saludables (57.7%)** los grupos más grandes, lo que requiere estrategias de marketing diferenciadas.

## 🚀 Recomendaciones Estratégicas (Fase Actuar)

Algunas de las conclusiones se tradujeron en recomendaciones específicas para Bellabeat, enfocadas en:
* **Materiales y Batería:** Promocionar la **resistencia y larga duración** a los clientes "Fuertes" y "Saludables".
* **Diseño y Sueño:** Enfocar el **diseño elegante** y la **monitorización de sueño** para los clientes "Sedentarios" con el objetivo de aumentar la comodidad y la consistencia de uso.

---

* **Autor:** Mauricio Villanueva
* **LinkedIn:** https://linkedin.com/in/mauricio-villanueva-rivera 
* **Tableau:** https://public.tableau.com/app/profile/mauricio.villanueva
* **Kaggle:** https://www.kaggle.com/mvr513 