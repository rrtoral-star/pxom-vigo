"""
Cliente para API oficial del Catastro Español (JSON)
Versión corregida - Estructura JSON verificada con respuestas reales
"""

import requests
from typing import Optional, Dict, List
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import unicodedata


def normalizar_texto_catastro(texto: str) -> str:
    """Normaliza texto para Catastro: quita acentos, mayúsculas"""
    if not texto:
        return texto
    
    texto_nfd = unicodedata.normalize('NFD', texto)
    texto_sin_acentos = ''.join(
        char for char in texto_nfd 
        if unicodedata.category(char) != 'Mn'
    )
    
    return texto_sin_acentos.upper()

class CatastroClient:
    """Cliente para consultas al Catastro (API oficial JSON)"""
    
    def __init__(self, cache_dir: str = "data/cache", debug: bool = False):
        # Endpoints
        self.base_url_wcf = "http://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero"
        self.base_url_asmx = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC"
        self.timeout = 15
        self.debug = debug
        
        # Cache local
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "catastro_cache.json"
        self._load_cache()
    
    def _log(self, msg: str, force: bool = False):
        """Log condicional según modo debug"""
        if self.debug or force:
            print(msg)
    
    def _load_cache(self):
        """Carga cache desde disco"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
        else:
            self.cache = {}
    
    def _save_cache(self):
        """Guarda cache a disco"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"⚠️  Error guardando cache: {e}")
    
    def consultar_por_coordenadas(self, lat: float, lon: float, 
                                    usar_proximidad: bool = True) -> Optional[Dict]:
        """
        Consulta parcela catastral por coordenadas
        
        Args:
            lat: Latitud WGS84
            lon: Longitud WGS84
            usar_proximidad: Si True, busca en radio de 50m si no hay resultado exacto
        
        Returns:
            dict con información catastral o None
        """
        
        # Cache key
        cache_key = f"coords_{lat:.6f}_{lon:.6f}"
        
        if cache_key in self.cache:
            self._log(f"   ✓ Catastro (cache): {cache_key}")
            return self.cache[cache_key]
        
        # Consultar con endpoint JSON (coordenadas exactas)
        resultado = self._consultar_coordenadas_json(lat, lon)
        
        # Si no hay resultado y usar_proximidad está activo, buscar en radio 50m
        if resultado is None and usar_proximidad:
            self._log("   → Buscando parcelas cercanas (radio 50m)...")
            resultado = self._consultar_coordenadas_proximidad(lat, lon)
        
        # Guardar en cache si hay resultado
        if resultado:
            self.cache[cache_key] = resultado
            self._save_cache()
        
        return resultado
    
    def _consultar_coordenadas_proximidad(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Busca parcelas en un radio de 50 metros usando Consulta_RCCOOR_Distancia
        """
        
        url = f"{self.base_url_wcf}/COVCCoordenadas.svc/json/Consulta_RCCOOR_Distancia"
        
        params = {
            'SRS': 'EPSG:4326',
            'CoorX': lon,
            'CoorY': lat
        }
        
        try:
            time.sleep(0.3)
            response = requests.get(url, params=params, timeout=self.timeout)
            
            self._log(f"   [DEBUG] URL proximidad: {response.url}")
            self._log(f"   [DEBUG] Status: {response.status_code}")
            
            if response.status_code != 200:
                self._log(f"   ❌ Error HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            # Estructura: Consulta_RCCOOR_DistanciaResult
            result_key = 'Consulta_RCCOOR_DistanciaResult'
            if result_key not in data:
                self._log(f"   ⚠️  Estructura no reconocida")
                return None
            
            result = data[result_key]
            
            # Verificar errores
            if 'lerr' in result and result['lerr']:
                errores = result['lerr']
                if isinstance(errores, list) and len(errores) > 0:
                    err = errores[0]
                    self._log(f"   ⚠️  Error proximidad [{err.get('cod')}]: {err.get('des')}")
                    return None
            
            # Extraer parcelas cercanas
            # Estructura real: coordenadas_distancias.coordd.lpcd[]
            if 'coordenadas_distancias' not in result:
                self._log(f"   ⚠️  No hay coordenadas en respuesta")
                return None
            
            coords = result['coordenadas_distancias']
            
            # coordd contiene geo y lpcd (lista de parcelas cercanas)
            coordd = coords.get('coordd', {})
            if isinstance(coordd, list):
                coordd = coordd[0] if coordd else {}
            
            # lpcd es la lista de parcelas por distancia
            lpcd = coordd.get('lpcd', [])
            
            if not lpcd:
                self._log(f"   ⚠️  Lista de parcelas vacía")
                return None
            
            if isinstance(lpcd, dict):
                lpcd = [lpcd]
            
            # Tomar la parcela más cercana (primera de la lista)
            parcela = lpcd[0]
            
            pc = parcela.get('pc', {})
            pc1 = pc.get('pc1', '')
            pc2 = pc.get('pc2', '')
            
            if not pc1 or not pc2:
                self._log(f"   ⚠️  RC incompleta en proximidad")
                return None
            
            ref_catastral = pc1 + pc2
            direccion = parcela.get('ldt', '')
            distancia = parcela.get('dis', '')
            
            self._log(f"   ✓ Parcela cercana: {ref_catastral} (a {distancia}m)")
            self._log(f"   ✓ Dirección: {direccion}")
            
            # Consultar datos completos
            resultado = self.consultar_por_referencia(ref_catastral)
            
            if resultado is None:
                resultado = {
                    'ref_catastral': ref_catastral,
                    'direccion': direccion
                }
            elif not resultado.get('direccion'):
                resultado['direccion'] = direccion
            
            # Añadir info de proximidad
            try:
                resultado['distancia_metros'] = float(distancia) if distancia else None
            except (ValueError, TypeError):
                resultado['distancia_metros'] = None
            resultado['busqueda_proximidad'] = True
            
            return resultado
            
        except Exception as e:
            self._log(f"   ❌ Error búsqueda proximidad: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None
    
    def _consultar_coordenadas_json(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Consulta usando endpoint WCF JSON
        
        Estructura respuesta verificada:
        {
          "Consulta_RCCOORResult": {
            "control": { "cucoor": 1 },
            "coordenadas": {
              "coord": [{
                "pc": { "pc1": "36045A0", "pc2": "2009018" },
                "geo": { "xcen": "...", "ycen": "...", "srs": "EPSG:4326" },
                "ldt": "Dirección..."
              }]
            }
          }
        }
        """
        
        url = f"{self.base_url_wcf}/COVCCoordenadas.svc/json/Consulta_RCCOOR"
        
        params = {
            'SRS': 'EPSG:4326',
            'CoorX': lon,  # Longitud = X
            'CoorY': lat   # Latitud = Y
        }
        
        try:
            self._log(f"   → Consultando coordenadas...")
            time.sleep(0.3)
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            self._log(f"   [DEBUG] URL: {response.url}")
            self._log(f"   [DEBUG] Status: {response.status_code}")
            
            if response.status_code != 200:
                self._log(f"   ❌ Error HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            # Estructura correcta: Consulta_RCCOORResult
            if 'Consulta_RCCOORResult' not in data:
                self._log(f"   ⚠️  Respuesta sin estructura esperada")
                self._log(f"   [DEBUG] Keys: {list(data.keys())}")
                return None
            
            result = data['Consulta_RCCOORResult']
            
            # Verificar errores (estructura: lerr[0].cod, lerr[0].des)
            if 'lerr' in result and result['lerr']:
                errores = result['lerr']
                if isinstance(errores, list) and len(errores) > 0:
                    err = errores[0]
                    self._log(f"   ⚠️  Error Catastro [{err.get('cod')}]: {err.get('des')}")
                    return None
            
            # Extraer coordenadas - estructura: coordenadas.coord[0]
            if 'coordenadas' not in result:
                self._log(f"   ⚠️  No hay datos de coordenadas en respuesta")
                return None
            
            coordenadas = result['coordenadas']
            
            if 'coord' not in coordenadas or not coordenadas['coord']:
                self._log(f"   ⚠️  No se encontró parcela en coordenadas")
                return None
            
            coord_list = coordenadas['coord']
            if isinstance(coord_list, list):
                coord = coord_list[0]
            else:
                coord = coord_list
            
            # Extraer referencia catastral (pc.pc1 + pc.pc2)
            pc = coord.get('pc', {})
            pc1 = pc.get('pc1', '')
            pc2 = pc.get('pc2', '')
            
            if not pc1 or not pc2:
                self._log(f"   ⚠️  Referencia catastral incompleta")
                return None
            
            ref_catastral = pc1 + pc2
            direccion = coord.get('ldt', '')
            
            self._log(f"   ✓ Ref. Catastral: {ref_catastral}")
            self._log(f"   ✓ Dirección: {direccion}")
            
            # Consultar datos completos por RC
            resultado = self.consultar_por_referencia(ref_catastral)
            
            # Si no hay datos completos, devolver al menos lo básico
            if resultado is None:
                resultado = {
                    'ref_catastral': ref_catastral,
                    'direccion': direccion
                }
            elif not resultado.get('direccion'):
                resultado['direccion'] = direccion
            
            return resultado
            
        except requests.exceptions.RequestException as e:
            self._log(f"   ❌ Error de conexión: {e}")
            return None
        except json.JSONDecodeError as e:
            self._log(f"   ❌ Error parseando JSON: {e}")
            return None
        except Exception as e:
            self._log(f"   ❌ Error inesperado: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None
    
    def consultar_por_referencia(self, ref_catastral: str) -> Optional[Dict]:
        """
        Consulta información por referencia catastral
        
        Args:
            ref_catastral: Referencia catastral (14 o 20 dígitos)
        
        Returns:
            dict con información de la parcela
        """
        
        # Limpiar referencia
        ref_catastral = ref_catastral.replace(' ', '').strip().upper()
        
        # Cache key
        cache_key = f"ref_{ref_catastral}"
        
        if cache_key in self.cache:
            self._log(f"   ✓ Catastro (cache): {ref_catastral}")
            return self.cache[cache_key]
        
        # Consultar con endpoint JSON
        resultado = self._consultar_referencia_json(ref_catastral)
        
        # Cache
        if resultado:
            self.cache[cache_key] = resultado
            self._save_cache()
        
        return resultado
    
    def _consultar_referencia_json(self, ref_catastral: str) -> Optional[Dict]:
        """
        Consulta datos por RC usando endpoint JSON
        
        Extrae todos los datos disponibles de la ficha catastral:
        - Datos de identificación
        - Localización completa
        - Superficie de suelo y construida
        - Año de construcción
        - Tipo de parcela
        - Lista de construcciones por planta
        - URL de cartografía
        """
        
        url = f"{self.base_url_wcf}/COVCCallejero.svc/json/Consulta_DNPRC"
        
        params = {
            'RefCat': ref_catastral
        }
        
        try:
            self._log(f"   → Consultando datos catastrales...")
            time.sleep(0.3)
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code != 200:
                self._log(f"   ❌ Error HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            # Estructura correcta: consulta_dnprcResult (con sufijo Result)
            result_key = 'consulta_dnprcResult'
            if result_key not in data:
                result_key = 'consulta_dnprc'
                if result_key not in data:
                    self._log(f"   ⚠️  Estructura de respuesta no reconocida")
                    self._log(f"   [DEBUG] Keys: {list(data.keys())}")
                    return None
            
            consulta = data[result_key]
            
            # Verificar errores
            if 'lerr' in consulta and consulta['lerr']:
                errores = consulta['lerr']
                if isinstance(errores, list) and len(errores) > 0:
                    err = errores[0]
                    self._log(f"   ⚠️  Error Catastro [{err.get('cod')}]: {err.get('des')}")
                    return None
            
            # Extraer datos del bien inmueble
            bico = consulta.get('bico')
            if not bico:
                self._log(f"   ⚠️  Sin datos de inmueble para {ref_catastral}")
                return None
            
            if isinstance(bico, list):
                bico = bico[0] if bico else {}
            
            bi = bico.get('bi', {})
            if isinstance(bi, list):
                bi = bi[0] if bi else {}
            
            # ====== CONSTRUIR RESULTADO COMPLETO ======
            resultado = {
                'ref_catastral': ref_catastral
            }
            
            # --- Identificación ---
            idbi = bi.get('idbi', {})
            resultado['tipo_inmueble'] = 'Urbano' if idbi.get('cn') == 'UR' else 'Rústico'
            
            # --- Dirección completa ---
            if 'ldt' in bi:
                resultado['direccion'] = bi['ldt']
            
            dt = bi.get('dt', {})
            resultado['provincia'] = dt.get('np')
            resultado['municipio'] = dt.get('nm')
            
            # Extraer código postal y detalles de dirección
            locs = dt.get('locs', {})
            lous = locs.get('lous', {})
            lourb = lous.get('lourb', {})
            
            resultado['codigo_postal'] = lourb.get('dp')
            
            dir_info = lourb.get('dir', {})
            resultado['tipo_via'] = dir_info.get('tv')
            resultado['nombre_via'] = dir_info.get('nv')
            resultado['numero'] = dir_info.get('pnp')
            
            # --- Datos del bien inmueble ---
            debi = bi.get('debi', {})
            if debi:
                resultado['uso'] = debi.get('luso')
                
                # Superficie construida
                sfc = debi.get('sfc')
                if sfc:
                    try:
                        resultado['superficie_construida'] = float(str(sfc).replace(',', '.'))
                    except ValueError:
                        pass
                
                # Año construcción
                ant = debi.get('ant')
                if ant:
                    resultado['ano_construccion'] = str(ant)
                
                # Coeficiente participación
                cpt = debi.get('cpt')
                if cpt:
                    try:
                        resultado['coeficiente_participacion'] = float(str(cpt).replace(',', '.'))
                    except ValueError:
                        pass
            
            # --- Datos de la finca/parcela ---
            finca = bico.get('finca', {})
            if finca:
                resultado['tipo_finca'] = finca.get('ltp')
                resultado['direccion_finca'] = finca.get('ldt')
                
                # Superficie de suelo
                dff = finca.get('dff', {})
                if isinstance(dff, dict):
                    ss = dff.get('ss') or dff.get('ssf', {}).get('ss')
                    if ss:
                        try:
                            resultado['superficie_suelo'] = float(str(ss).replace(',', '.'))
                        except ValueError:
                            pass
                
                # URL de cartografía
                infgraf = finca.get('infgraf', {})
                if infgraf:
                    resultado['url_cartografia'] = infgraf.get('igraf')
            
            # --- Lista de construcciones ---
            lcons = bico.get('lcons', [])
            if lcons:
                if isinstance(lcons, dict):
                    lcons = lcons.get('cons', [])
                
                if isinstance(lcons, list) and len(lcons) > 0:
                    construcciones = []
                    superficie_total = 0
                    
                    for cons in lcons:
                        c = {}
                        c['uso'] = cons.get('lcd')
                        c['tipo'] = cons.get('dvcons', {}).get('dtip')
                        
                        # Superficie
                        stl = cons.get('dfcons', {}).get('stl')
                        if stl:
                            try:
                                sup = float(str(stl).replace(',', '.'))
                                c['superficie'] = sup
                                superficie_total += sup
                            except ValueError:
                                pass
                        
                        # Localización (escalera, planta, puerta)
                        dt_cons = cons.get('dt', {})
                        lourb_cons = dt_cons.get('lourb', {})
                        loint = lourb_cons.get('loint', {})
                        
                        c['escalera'] = loint.get('es')
                        c['planta'] = loint.get('pt')
                        c['puerta'] = loint.get('pu')
                        
                        construcciones.append(c)
                    
                    resultado['construcciones'] = construcciones
                    resultado['num_construcciones'] = len(construcciones)
                    resultado['superficie_total_construida'] = superficie_total
                    
                    # Resumen por uso
                    usos = {}
                    for c in construcciones:
                        uso = c.get('uso', 'OTRO')
                        if uso not in usos:
                            usos[uso] = {'count': 0, 'superficie': 0}
                        usos[uso]['count'] += 1
                        usos[uso]['superficie'] += c.get('superficie', 0)
                    resultado['resumen_usos'] = usos
            
            self._log(f"   ✓ Datos obtenidos para {ref_catastral}")
            return resultado
            
        except Exception as e:
            self._log(f"   ❌ Error consultando RC: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None
    def buscar_calle(self, provincia: str, municipio: str, nombre_parcial: str) -> list:
        """
        Busca calles en el Catastro por nombre parcial
        
        Returns:
            Lista de calles encontradas con nombre exacto y tipo
        """
        
        url = "http://ovc.catastro.meh.es/ovcservweb/OVCCallejero.asmx/ConsultaVia"
        
        params = {
            'Provincia': provincia,
            'Municipio': municipio,
            'TipoVia': '',
            'NombreVia': nombre_parcial
        }
        
        try:
            print(f"   → Buscando calle '{nombre_parcial}' en Catastro...")
            response = requests.get(url, params=params, timeout=self.timeout)
            
            # DEBUG: Ver respuesta cruda
            print(f"\n[DEBUG] Status: {response.status_code}")
            print(f"[DEBUG] Response XML (primeros 500 chars):")
            print(response.text[:500])
            print("\n")
        
            if response.status_code != 200:
                if response.status_code != 200:
                    return []
                
                # Parsear XML
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                calles = []
                for via in root.findall('.//via'):
                    calle = {
                        'tipo': via.find('loine/tv').text if via.find('loine/tv') is not None else '',
                        'nombre': via.find('loine/nv').text if via.find('loine/nv') is not None else ''
                    }
                    calles.append(calle)
                    print(f"      {calle['tipo']} {calle['nombre']}")
                
                return calles
        
        except Exception as e:
            print(f"   Error buscando calle: {e}")
            return []
        
    def consultar_por_direccion(self, provincia: str, municipio: str, 
                                 tipo_via: str, nombre_via: str, 
                                 numero: str) -> Optional[Dict]:
        """
        Consulta parcela por dirección
        Si hay múltiples unidades, las obtiene todas
        """
        
        url = f"{self.base_url_wcf}/COVCCallejero.svc/json/Consulta_DNPLOC"

        # Eliminar artículos gallegos/españoles que el Catastro no reconoce
        _ARTICULOS = ('DO ', 'DA ', 'DOS ', 'DAS ', 'DE O ', 'DE A ',
                      'DEL ', 'DE ', 'DE LA ', 'DE LOS ', 'DE LAS ',
                      "D'", 'EL ', 'LA ', 'LOS ', 'LAS ')
        nombre_limpio = nombre_via.strip()
        nombre_upper = nombre_limpio.upper()
        for art in _ARTICULOS:
            if nombre_upper.startswith(art):
                nombre_limpio = nombre_limpio[len(art):]
                break

        nombre_via_normalizado = normalizar_texto_catastro(nombre_limpio)

        params = {
            'Provincia': provincia,
            'Municipio': municipio,
            'Sigla': tipo_via,
            'Calle': nombre_via_normalizado,
            'Numero': numero
        }

        self._log(f"   → Consultando dirección: {tipo_via} {nombre_via_normalizado} {numero}")
        
        try:
            self._log(f"   → Consultando por dirección...")
            time.sleep(0.3)
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Verificar estructura
            if 'consulta_dnplocResult' in data:
                result_key = 'consulta_dnplocResult'
            elif 'consulta_dnpResult' in data:
                result_key = 'consulta_dnpResult'
            else:
                result_key = 'consulta_dnp'
            
            if result_key not in data:
                return None
            
            consulta = data[result_key]
            
            # Caso 1: Lista de inmuebles
            if 'lrcdnp' in consulta:
                    
                lrcdnp = consulta['lrcdnp']
                rcdnp_list = lrcdnp.get('rcdnp', [])
                    
                if not isinstance(rcdnp_list, list):
                    rcdnp_list = [rcdnp_list]
                    
                refs = []
                for rcdnp in rcdnp_list:
                    if 'rc' in rcdnp:
                        rc = rcdnp['rc']
                        ref = (rc.get('pc1', '') + 
                               rc.get('pc2', '') + 
                               rc.get('car', '') + 
                               rc.get('cc1', '') + 
                                rc.get('cc2', ''))
                        if ref:
                           refs.append(ref)
                    
                
                if refs:
                    todas_construcciones = []
                    resultado_combinado = None
                    
                    for ref in refs:
                        resultado = self.consultar_por_referencia(ref)
                        
                        if resultado:
                            if not resultado_combinado:
                                resultado_combinado = resultado.copy()
                            
                            if resultado.get('construcciones'):
                                 # Añadir ref catastral a cada construcción
                                 for c in resultado['construcciones']:
                                    c['ref_catastral'] = ref
                                 todas_construcciones.extend(resultado['construcciones'])
                    
                    if resultado_combinado and todas_construcciones:
                        resultado_combinado['construcciones'] = todas_construcciones
                        resultado_combinado['num_construcciones'] = len(todas_construcciones)
                        resultado_combinado['superficie_total_construida'] = sum(
                            c.get('superficie', 0) for c in todas_construcciones
                        )
                        
                        usos = {}
                        for c in todas_construcciones:
                            uso = c.get('uso', 'OTRO')
                            if uso not in usos:
                                usos[uso] = {'count': 0, 'superficie': 0}
                            usos[uso]['count'] += 1
                            usos[uso]['superficie'] += c.get('superficie', 0)
                        resultado_combinado['resumen_usos'] = usos
                        
                        resultado_combinado['referencias_multiples'] = refs
                        resultado_combinado['num_referencias'] = len(refs)
                        
                        return resultado_combinado
            
            # Caso 2: Datos directos (inmueble único)
            elif 'bico' in consulta:
                bi = consulta['bico'].get('bi', {})
                
                if 'idbi' in bi and 'rc' in bi['idbi']:
                    rc = bi['idbi']['rc']
                    ref = (rc.get('pc1', '') + 
                           rc.get('pc2', '') + 
                           rc.get('car', '') + 
                           rc.get('cc1', '') + 
                           rc.get('cc2', ''))
                    
                    if ref:
                        resultado = self.consultar_por_referencia(ref)
                        
                        # Añadir ref_catastral a cada construcción
                        if resultado and resultado.get('construcciones'):
                            for c in resultado['construcciones']:
                                c['ref_catastral'] = ref
                        
                        return resultado
            
            return None
            
        except Exception as e:
            print(f"[DEBUG] Error: {e}\n")
            return None
    

    def consultar_parcela_completa(self, ref_parcela_14: str) -> Optional[Dict]:
            """
            Consulta TODAS las unidades de una parcela (14 dígitos)
            
            Args:
                ref_parcela_14: Referencia parcela (14 dígitos: pc1+pc2)
            
            Returns:
                dict con todas las unidades de la parcela
            """
            
            try:
                # Usar endpoint que devuelve todas las unidades de una parcela
                resultado = self.consultar_por_referencia(ref_parcela_14)
                
                if resultado and resultado.get('construcciones'):
                    return resultado
                
                return None
                
            except Exception as e:
                print(f"Error consultando parcela completa: {e}")
                return None

    def buscar_calles(self, provincia: str, municipio: str, 
                      nombre_parcial: str) -> Optional[List[Dict]]:
        """
        Busca calles por nombre parcial
        
        Args:
            provincia: Nombre de la provincia
            municipio: Nombre del municipio
            nombre_parcial: Parte del nombre de la calle
        
        Returns:
            Lista de calles encontradas
        """
        
        # Usar endpoint ASMX (el WCF/json da 404 para ConsultaVia)
        url = f"{self.base_url_asmx}/OVCCallejero.asmx/ConsultaVia"
        
        params = {
            'Provincia': provincia.upper(),
            'Municipio': municipio.upper(),
            'TipoVia': '',
            'NombreVia': nombre_parcial.upper()
        }
        
        try:
            self._log(f"   → Buscando calles...")
            self._log(f"   [DEBUG] Params: {params}")
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            self._log(f"   [DEBUG] URL: {response.url}")
            self._log(f"   [DEBUG] Status: {response.status_code}")
            
            if response.status_code != 200:
                self._log(f"   ❌ Error HTTP {response.status_code}")
                return None
            
            # Este endpoint devuelve XML
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                self._log(f"   ❌ Error XML: {e}")
                return None
            
            # Namespace del catastro
            ns = {'cat': 'http://www.catastro.meh.es/'}
            
            # Buscar errores
            err = root.find('.//cat:err', ns)
            if err is not None:
                des = err.find('cat:des', ns)
                if des is not None:
                    self._log(f"   ⚠️  Error: {des.text}")
                    return None
            
            # Estructura real: callejero/calle[]/dir/{tv,nv,cv}
            calles = []
            
            # Buscar todas las calles
            calle_elems = root.findall('.//cat:calle', ns)
            
            for calle in calle_elems:
                dir_elem = calle.find('cat:dir', ns)
                if dir_elem is not None:
                    tv = dir_elem.find('cat:tv', ns)
                    nv = dir_elem.find('cat:nv', ns)
                    cv = dir_elem.find('cat:cv', ns)
                    
                    calles.append({
                        'tipo': tv.text if tv is not None else '',
                        'nombre': nv.text if nv is not None else '',
                        'codigo': cv.text if cv is not None else ''
                    })
            
            self._log(f"   ✓ Encontradas {len(calles)} calles")
            return calles if calles else None
            
        except Exception as e:
            self._log(f"   ❌ Error buscando calles: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None
    
    def limpiar_cache(self):
        """Limpia toda la cache"""
        self.cache = {}
        self._save_cache()
        self._log("   ✓ Cache limpiada", force=True)
    
    def obtener_ficha_completa(self, ref_catastral: str = None, 
                                lat: float = None, lon: float = None,
                                direccion: dict = None) -> Optional[Dict]:
        """
        Obtiene la ficha catastral completa de un inmueble.
        
        Puedes especificar la búsqueda de 3 formas:
        
        1. Por referencia catastral:
           ficha = client.obtener_ficha_completa(ref_catastral="3362013NG2736S0001RB")
        
        2. Por coordenadas:
           ficha = client.obtener_ficha_completa(lat=42.2406, lon=-8.7207)
        
        3. Por dirección:
           ficha = client.obtener_ficha_completa(direccion={
               'provincia': 'PONTEVEDRA',
               'municipio': 'VIGO', 
               'tipo_via': 'RU',
               'nombre_via': 'URZAIZ',
               'numero': '1'
           })
        
        Returns:
            dict con todos los datos de la ficha catastral:
            - ref_catastral, tipo_inmueble, tipo_finca
            - direccion, provincia, municipio, codigo_postal
            - uso, ano_construccion
            - superficie_suelo, superficie_total_construida
            - construcciones (lista detallada)
            - resumen_usos
            - url_cartografia
        """
        
        if ref_catastral:
            return self.consultar_por_referencia(ref_catastral)
        
        elif lat is not None and lon is not None:
            return self.consultar_por_coordenadas(lat, lon)
        
        elif direccion:
            return self.consultar_por_direccion(
                provincia=direccion.get('provincia', ''),
                municipio=direccion.get('municipio', ''),
                tipo_via=direccion.get('tipo_via', ''),
                nombre_via=direccion.get('nombre_via', ''),
                numero=direccion.get('numero', '')
            )
        
        else:
            self._log("   ❌ Debes especificar ref_catastral, coordenadas (lat/lon) o direccion", force=True)
            return None

    def consultar_parcela_por_ref(self, ref_14: str) -> Optional[Dict]:
            """Consulta TODA la parcela por referencia de 14 dígitos"""
            
            print(f"\n[DEBUG] Consultando parcela completa: {ref_14}")
            
            url = f"{self.base_url_wcf}/COVCCoordenadas.svc/json/Consulta_RCCOOR"
            
            params = {
                'SRS': 'EPSG:4326',
                'RC': ref_14
            }
            
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[DEBUG] Response keys: {list(data.keys())}")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
                    
                    return data
                
                return None
                
            except Exception as e:
                print(f"[DEBUG] Error: {e}")
                return None

def test_catastro():
    """Prueba cliente Catastro corregido"""
    
    print("\n" + "="*70)
    print("TEST CLIENTE CATASTRO (COMPLETO)")
    print("="*70)
    
    # Crear cliente con debug activado
    client = CatastroClient(debug=True)
    
    # Limpiar cache para obtener datos actualizados
    client.limpiar_cache()
    
    # Test 1: Coordenadas que SÍ funcionan (verificadas en debug)
    print("\n1. Consulta por coordenadas (Redondela/Pontevedra):")
    lat, lon = 42.28137302193453, -8.588562011718752
    print(f"   Coords: {lat}, {lon}")
    
    resultado = client.consultar_por_coordenadas(lat, lon)
    
    if resultado:
        print(f"\n   ✅ Datos obtenidos:")
        print(f"      Ref. Catastral: {resultado.get('ref_catastral')}")
        print(f"      Dirección: {resultado.get('direccion')}")
        print(f"      Uso: {resultado.get('uso')}")
        if resultado.get('superficie_suelo'):
            print(f"      Superficie suelo: {resultado.get('superficie_suelo'):.2f} m²")
        if resultado.get('superficie_construida'):
            print(f"      Superficie construida: {resultado.get('superficie_construida'):.2f} m²")
        print(f"      Año construcción: {resultado.get('ano_construccion')}")
    else:
        print(f"   ⚠️  No se obtuvo información")
    
    # Test 2: Vigo centro (fallará exacto pero encontrará por proximidad)
    print("\n2. Consulta Vigo centro (con fallback a proximidad):")
    lat2, lon2 = 42.2406, -8.7207
    print(f"   Coords: {lat2}, {lon2}")
    
    resultado2 = client.consultar_por_coordenadas(lat2, lon2)
    
    if resultado2:
        print(f"   ✅ Ref: {resultado2.get('ref_catastral')}")
        print(f"   Dirección: {resultado2.get('direccion')}")
        print(f"   Uso: {resultado2.get('uso')}")
        if resultado2.get('busqueda_proximidad'):
            print(f"   📍 Encontrado por proximidad a {resultado2.get('distancia_metros')}m")
    else:
        print(f"   ⚠️  Sin datos (ni exactos ni por proximidad)")
    
    # Test 3: Búsqueda de calles primero
    print("\n3. Buscar calles que contengan 'URZAIZ' en Vigo:")
    calles = client.buscar_calles(
        provincia="PONTEVEDRA",
        municipio="VIGO",
        nombre_parcial="URZAIZ"
    )
    
    if calles:
        print(f"   ✅ Encontradas {len(calles)} calles:")
        for calle in calles[:5]:
            print(f"      - {calle.get('tipo')} {calle.get('nombre')}")
    else:
        print(f"   ⚠️  No se encontraron calles")
    
    # Test 4: Búsqueda por dirección - FICHA COMPLETA
    print("\n4. FICHA CATASTRAL COMPLETA (Urzaiz 1, Vigo):")
    if calles and len(calles) > 0:
        calle_encontrada = calles[0]
        print(f"   Buscando: {calle_encontrada.get('tipo')} {calle_encontrada.get('nombre')} 1")
        
        ficha = client.consultar_por_direccion(
            provincia="PONTEVEDRA",
            municipio="VIGO",
            tipo_via=calle_encontrada.get('tipo', 'CL'),
            nombre_via=calle_encontrada.get('nombre', 'URZAIZ'),
            numero="1"
        )
        
        if ficha:
            print(f"\n   {'='*50}")
            print(f"   DATOS DE IDENTIFICACIÓN")
            print(f"   {'='*50}")
            print(f"   Ref. Catastral: {ficha.get('ref_catastral')}")
            print(f"   Tipo: {ficha.get('tipo_inmueble')}")
            print(f"   Tipo finca: {ficha.get('tipo_finca')}")
            
            print(f"\n   {'='*50}")
            print(f"   LOCALIZACIÓN")
            print(f"   {'='*50}")
            print(f"   Dirección: {ficha.get('direccion')}")
            print(f"   Vía: {ficha.get('tipo_via')} {ficha.get('nombre_via')} {ficha.get('numero')}")
            print(f"   CP: {ficha.get('codigo_postal')}")
            print(f"   Municipio: {ficha.get('municipio')}")
            print(f"   Provincia: {ficha.get('provincia')}")
            
            print(f"\n   {'='*50}")
            print(f"   CARACTERÍSTICAS")
            print(f"   {'='*50}")
            print(f"   Uso principal: {ficha.get('uso')}")
            print(f"   Año construcción: {ficha.get('ano_construccion')}")
            print(f"   Superficie suelo: {ficha.get('superficie_suelo')} m²")
            print(f"   Superficie construida total: {ficha.get('superficie_total_construida')} m²")
            print(f"   Coef. participación: {ficha.get('coeficiente_participacion')}")
            
            if ficha.get('resumen_usos'):
                print(f"\n   {'='*50}")
                print(f"   RESUMEN POR USOS")
                print(f"   {'='*50}")
                for uso, datos in ficha.get('resumen_usos', {}).items():
                    print(f"   {uso}: {datos['count']} unidades, {datos['superficie']:.0f} m²")
            
            if ficha.get('construcciones'):
                print(f"\n   {'='*50}")
                print(f"   CONSTRUCCIONES ({ficha.get('num_construcciones')})")
                print(f"   {'='*50}")
                for i, c in enumerate(ficha.get('construcciones', [])[:10]):  # Mostrar max 10
                    planta = c.get('planta', '?')
                    puerta = c.get('puerta', '?')
                    print(f"   {i+1}. {c.get('uso')}: Planta {planta}, Puerta {puerta} - {c.get('superficie', 0):.0f} m²")
                if ficha.get('num_construcciones', 0) > 10:
                    print(f"   ... y {ficha.get('num_construcciones') - 10} más")
            
            if ficha.get('url_cartografia'):
                print(f"\n   🗺️  Mapa: {ficha.get('url_cartografia')}")
        else:
            print(f"   ⚠️  No encontrado")
    
    # Test 5: Cache
    print("\n5. Test de cache:")
    resultado_cache = client.consultar_por_coordenadas(lat, lon)
    if resultado_cache:
        print(f"   ✅ Cache funcionando correctamente")
    
    print("\n" + "="*70)
    print("CLIENTE CATASTRO COMPLETO")
    print(f"Cache: {client.cache_file}")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_catastro()