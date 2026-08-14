# Documentos legales de PlanGasto

Sitio estático con los Términos de Uso y la Política de Privacidad de
[PlanGasto](https://play.google.com/store/apps/details?id=com.eduardolivorevelo.gastoplan),
en español e inglés.

Este repositorio es público **solo porque las tiendas exigen que estos
documentos estén accesibles en una URL pública y estable**. El código fuente de
la aplicación vive en otro repositorio y sigue siendo privado.

## URLs publicadas

| | Español | English |
|---|---|---|
| Privacidad | `/es/privacidad/` | `/en/privacy/` |
| Términos | `/es/terminos/` | `/en/terms/` |

Estas son las direcciones que consumen:

- La ficha de Google Play y de App Store Connect (campo *Privacy Policy URL*).
- El pie legal del paywall de la aplicación, en
  `lib/core/monetization/legal_links.dart`.

**No renombres ni muevas estas rutas.** Una URL legal que devuelve 404 es un
motivo de rechazo en las dos tiendas, y las fichas ya publicadas apuntan aquí.

## Cómo se actualiza

La fuente única de verdad **no está en este repositorio**: son los cuatro
Markdown de `legal/` en el repositorio de la aplicación. Aquí solo vive el HTML
generado.

```bash
python3 build.py ../gestor_gastos_app_mig
```

El script regenera `es/`, `en/` e `index.html`. Después, commit y push: GitHub
Pages publica la rama por defecto.

No edites el HTML a mano. Se sobrescribe en la siguiente generación, y dejaría
el documento publicado diciendo algo distinto de lo que dice el original.

## Regla que no se salta

Lo que dicen estos documentos tiene que ser cierto en la aplicación. Si cambian
los límites de la versión gratuita, lo que desbloquea Pro, las dependencias o
el tratamiento de datos, **primero se actualizan los Markdown del repositorio de
la app y después se regenera esto**.

Una contradicción entre lo que hace el código y lo que promete el documento
publicado es exactamente lo que bloquea una revisión de tienda.
