/*
 * Tarea CG 2 - Archivo Javacript para la creación del archivo .obj del edificio
 *
 * Jin Sik Yoon, A01026630
 * 2025-11-19
 */

"use strict";
const fs = require('fs'); // Módulo para manejo de archivos

// -----
// Lectura de argumentos y validación
// -----

// Leer el input del usuario y guarda en el arreglo
const [ladosArg, alturaArg, bottomArg, topArg] = process.argv.slice(2);
// process.argv.slice(2) nos ayuda a ignorar los dos primeros elementos porque los necesarios son los valores nada más

// Ya que los argumentes son String, convertimos a un número
let lados = Number(ladosArg) || 8;
let altura = Number(alturaArg) || 6.0;
let radioBottom = Number(bottomArg) || 1.0;
let radioTop = Number(topArg) || 0.8;
// Si la conversión es inválida, se asignan valores por defecto

// Ajustar a rangos válidos para que los valores sean razonables
if (lados < 3) lados = 3;
if (lados > 36) lados = 36;
if (altura <= 0) altura = 6.0;
if (radioBottom <= 0) radioBottom = 1.0;
if (radioTop <= 0) radioTop = 0.8;

// -----
// Utilidades para formato OBJ
// -----

// Función de normalizar el vector (x, y, z)
function normalize(x, y, z) {
    const longitud = Math.sqrt(x * x + y * y + z * z);
    if (longitud == 0) return [0, 0, 0];
    return [x / longitud, y / longitud, z / longitud];
}

// Función para calcular la normal de un triángulo dado por tres vértices
function calcularNormal(v0, v1, v2) {
    // Obtenemos los lados del triángulo
    // De vértice 0 a vértice 1: u
    const ux = v1.x - v0.x;
    const uy = v1.y - v0.y;
    const uz = v1.z - v0.z;
    // De vértice 0 a vértice 2: v
    const vx = v2.x - v0.x;
    const vy = v2.y - v0.y;
    const vz = v2.z - v0.z;

    // Producto cruz para obtener el vector normal
    const nx = uy * vz - uz * vy;
    const ny = uz * vx - ux * vz;
    const nz = ux * vy - uy * vx;

    // Normaliza el vector
    return normalize(nx, ny, nz);
}

// Función de cambiar un número a un texto para salida en OBJ
function cambioNumATexto(n) {
    const redondeado = Math.round(n * 10000) / 10000; // Redondear a 4 decimales
    return String(redondeado);
}

// -----
// Generación de vértices
// 1 vértice por cada esquina + 2 centros (top y bottom)
// -----

const vertices = [null]; // Arreglo donde guarda las coordenadas de los vértices
// Lo lleno el primer índice con null para que los índices coincidan con los del OBJ (Por la convención)
const verticeLinea = []; // Arreglo donde guarda las líneas de vértices en formato OBJ (v 0.0000 0.0000 0.0000)

// Función para agregar un vértice en el arreglo de vértices
function agregarVertice(x, y, z) {
  vertices.push({x, y, z});
  verticeLinea.push(`v ${cambioNumATexto(x)} ${cambioNumATexto(y)} ${cambioNumATexto(z)}`);
}

// Centro inferior por default (índice 1)
agregarVertice(0.0, 0.0, 0.0);
// Centro superior por default (índice 2)
agregarVertice(0.0, altura, 0.0);

// Vértices alrededor de los centros depende de la cantidad de lados
for (let i = 0; i < lados; i++) {
    // Ángulo para el vértice que estamos calculando
    const angulo = (2 * Math.PI * i) / lados;
    const coseno = Math.cos(angulo);
    const seno = Math.sin(angulo);

    // Vértices en el bottom (y = 0)
    const xBottom = radioBottom * coseno;
    const zBottom = radioBottom * seno;
    agregarVertice(xBottom, 0.0, zBottom);

    // Vértices en el top (y = altura)
    const xTop = radioTop * coseno;
    const zTop = radioTop * seno;
    agregarVertice(xTop, altura, zTop);
}

// -----
// Generación de normales y caras
// -----

const normalLinea = []; // Arreglo donde guarda las líneas de normales en formato OBJ (vn 0.0000 0.0000 0.0000)
const caraLinea = []; // Arreglo donde guarda las líneas de caras en formato OBJ (f v1//n v2//n v3//n)

// Función para agregar la normal al arreglo de normales
function agregarNormal(nx, ny, nz) {
    normalLinea.push(`vn ${cambioNumATexto(nx)} ${cambioNumATexto(ny)} ${cambioNumATexto(nz)}`);
    return normalLinea.length; // índice de esta normal
}

// Función para agregar la cara al arreglo de caras
function agregarCara(i1, i2, i3, idx) {
    caraLinea.push(`f ${i1}//${idx} ${i2}//${idx} ${i3}//${idx}`);
}

const centroBottom = 1; // Índice del centro inferior
const centroTop = 2; // Índice del centro superior

// Dibujamos las caras
// Bottom face (y = 0), normal (0, -1, 0)

for (let i = 0; i < lados; i++) {
    const actualBottom = 3 + 2 * i; // Vértice actual en el bottom
    const siguienteBottom = 3 + 2 * ((i + 1) % lados); // Vértice siguiente en el bottom

    const idx = agregarNormal(0.0, -1.0, 0.0);
    agregarCara(siguienteBottom, centroBottom, actualBottom, idx);
}

// Top face (y = altura), normal (0, 1, 0)

for (let i = 0; i < lados; i++) {
    const actualTop = 4 + 2 * i; // Vértice actual en el top
    const siguienteTop = 4 + 2 * ((i + 1) % lados); // Vértice siguiente en el top
  
    const idx = agregarNormal(0.0, 1.0, 0.0);
    agregarCara(actualTop, centroTop, siguienteTop, idx);
}

// Lateral faces

for (let i = 0; i < lados; i++) {
    // Vértices de la cara lateral
    const b0 = 3 + 2 * i; // bottom actual
    const t0 = 4 + 2 * i; // top actual
    const b1 = 3 + 2 * ((i + 1) % lados); // bottom siguiente
    const t1 = 4 + 2 * ((i + 1) % lados); // top siguiente
  
    // Triángulo 1: b1, b0, t0
    {
        // Obtener los vértices
        const v0 = vertices[b1];
        const v1 = vertices[b0];
        const v2 = vertices[t0];
        // Calcular la normal
        const [nx, ny, nz] = calcularNormal(v0, v1, v2);
        const idx = agregarNormal(nx, ny, nz);
        agregarCara(b1, b0, t0, idx);
    }

    // Triángulo 2: t0, t1, b1
    {
        // Obtener los vértices
        const v0 = vertices[t0];
        const v1 = vertices[t1];
        const v2 = vertices[b1];
        // Calcular la normal
        const [nx, ny, nz] = calcularNormal(v0, v1, v2);
        const idx = agregarNormal(nx, ny, nz);
        agregarCara(t0, t1, b1, idx);
    }
}

// -----
// Generación del archivo OBJ
// -----

const numVertices = verticeLinea.length - 1; // -1 porque el primer índice es null
const numNormals = normalLinea.length;
const numFaces = caraLinea.length;

let objText = "";

// Nombre de archivo basado en los parámetros
const archivo = `building_${lados}_${altura}_${radioBottom}_${radioTop}.obj`;

// Encabezado
objText += `# OBJ file ${archivo}\n`;
objText += `# ${numVertices} vertices\n`;
objText += verticeLinea.join("\n") + "\n";
objText += `# ${numNormals} normals\n`;
objText += normalLinea.join("\n") + "\n";
objText += `# ${numFaces} faces\n`;
objText += caraLinea.join("\n") + "\n";

// Escritura del archivo
fs.writeFileSync(archivo, objText, 'utf8');
console.log(`Archivo OBJ generado: ${archivo}`);