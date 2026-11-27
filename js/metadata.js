/**
 * Geoportal Regional da AMESC — Registro Central de Metadados (21 campos) & Legendas Didáticas.
 */
window.GeoMetadata = (() => {
  const CONSULTA_BASE = '27/11/2026';

  function makeMeta(o) {
    return {
      sourceClass: o.sourceClass || 'Oficial',
      whatIsThis: o.whatIsThis || 'Base geoespacial integrada da região AMESC (15 municípios do Extremo Sul Catarinense).',
      classHelp: o.classHelp || {},
      redistributable: o.redistributable !== undefined ? Boolean(o.redistributable) : true,
      metadata: {
        nome_camada: o.nome_camada || 'Não informado pela fonte',
        descricao: o.whatIsThis || o.descricao || 'Não informado pela fonte',
        categoria: o.categoria || 'Geoinformação Regional AMESC',
        orgao_responsavel: o.orgao_responsavel || 'Não informado pela fonte',
        instituicao_fornecedora: o.instituicao_fornecedora || o.orgao_responsavel || 'Não informado pela fonte',
        url_fonte_original: o.url_fonte_original || 'Não informado pela fonte',
        url_download_ou_servico: o.url_download_ou_servico || o.url_fonte_original || 'Não informado pela fonte',
        formato: o.formato || 'WFS / Shapefile → GeoJSON',
        tipo_geometria: o.tipo_geometria || 'Polígono',
        sistema_referencia_coordenadas: o.sistema_referencia_coordenadas || 'Origem: SIRGAS 2000 (EPSG:4674 / EPSG:31982) | Web: WGS 84 (EPSG:4326)',
        escala_cartografica: o.escala_cartografica || '1:25.000 / 1:50.000',
        resolucao_espacial: o.resolucao_espacial || 'Não aplicável (dado vetorial)',
        data_producao: o.data_producao || '2022–2025',
        data_atualizacao: o.data_atualizacao || '2026',
        data_consulta: o.data_consulta || CONSULTA_BASE,
        abrangencia_territorial: o.abrangencia_territorial || 'AMESC — 15 Municípios do Extremo Sul Catarinense (SC)',
        licenca_uso: o.licenca_uso || 'Dados Abertos Governamentais',
        restricoes_acesso: o.restricoes_acesso || 'Público (sem restrições de consulta)',
        metodo_obtencao: o.metodo_obtencao || 'Extração regional oficial, reprojeção para WGS 84, recorte AMESC e validação topológica.',
        observacoes_qualidade: o.observacoes_qualidade || 'Validado geograficamente sobre o mosaico oficial dos 15 municípios da AMESC.',
        status_validacao: o.status_validacao || 'DISPONÍVEL E VERIFICADO',
      },
    };
  }

  const CLASS_HELP_MAP = {
    amesc_setores_ibge: {
      Urbana: 'Setores censitários urbanos consolidados ou núcleos urbanos dos 15 municípios (IBGE Censo 2022).',
      Rural: 'Setores censitários rurais (áreas agrícolas, serranas e localidades do interior).',
    },
    amesc_fbds_uso_solo: {
      'formação florestal': 'Mata Atlântica nativa em estágio médio/avançado ou secundário.',
      'formação não florestal': 'Campos naturais, restingas herbáceas e áreas campestres de altitude.',
      silvicultura: 'Reflorestamento comercial (eucalipto e pinus).',
      'área antropizada': 'Rizicultura irrigada, bananicultura, pastagens, fumo, milho e áreas produtivas.',
      'área edificada': 'Cidades, sedes municipais, balneários e núcleos edificados.',
      'água': 'Rios principais, lagoas costeiras (Sombrio, Caverá) e reservatórios.',
    },
    amesc_fbds_app: {
      "curso d'água (0 - 10m)": 'Faixa marginal de 30 m de APP ao longo de córregos e riachos.',
      "curso d'água (10 - 50m)": 'Faixa marginal de 50 m de APP em rios de médio porte.',
      "curso d'água (50 - 200m)": 'Faixa marginal de 100 m de APP nos principais rios regionais.',
      "curso d'água (200 - 600m)": 'Faixa de 200 m de APP em estuários e trechos largos (Araranguá/Mampituba).',
      "massa d'água": 'Entorno de proteção de lagoas e reservatórios.',
      nascente: 'Raio de 50 m de preservação permanente ao redor de nascentes.',
    },
    amesc_setores_risco_sgb: {
      'Muito alto': 'Risco R4 — instabilidade severa ou histórico recorrente de desastres; prioridade máxima da Defesa Civil.',
      'Muito Alto': 'Risco R4 — instabilidade severa ou histórico recorrente de desastres; prioridade máxima da Defesa Civil.',
      Alto: 'Risco R3 — elevada probabilidade de inundação, enxurrada ou deslizamento em chuvas intensas.',
      'Médio': 'Risco R2 — condições predisponentes moderadas.',
      Baixo: 'Risco R1 — baixa probabilidade de ocorrência destrutiva.',
    },
    amesc_suscet_inundacao_sgb: {
      Alta: 'Planícies fluviais e áreas baixas com alta propensão natural a cheias e alagamentos.',
      'Média': 'Terraços e áreas intermediárias atingíveis em eventos de cheia intensa.',
      Baixa: 'Terrenos com baixa propensão natural a inundações.',
    },
    amesc_suscet_movmassa_sgb: {
      Alta: 'Encostas íngremes e escarpas da Serra Geral altamente suscetíveis a deslizamentos e quedas de rocha.',
      'Média': 'Vertentes de declividade moderada com suscetibilidade intermediária.',
      Baixa: 'Planícies e colinas suaves com baixa suscetibilidade.',
    },
    amesc_declividade_ima: {
      '0–5% (Plano)': 'Planícies costeiras e várzeas rizícolas; baixa erosão, maior risco de alagamento.',
      '5–12% (Suave)': 'Relevo suave ondulado; propício à ocupação urbana e agricultura mecanizada.',
      '12–25% (Ondulado)': 'Encostas moderadas; requer controle de drenagem e manejo conservacionista.',
      '25–45% (Forte)': 'Encostas íngremes; forte restrição à ocupação urbana.',
      '>45% (Escarpado)': 'Escarpa da Serra Geral / APP de declividade; risco crítico a escorregamentos.',
    },
    amesc_bacias_ima: {
      ARARANGUA: 'Bacia Hidrográfica do Rio Araranguá (principal bacia da AMESC).',
      MAMPITUBA: 'Bacia Hidrográfica do Rio Mampituba (divisa sul com o RS).',
      URUSSANGA: 'Bacia Hidrográfica do Rio Urussanga (extremo norte/nordeste da AMESC).',
    },
    amesc_fitogeografico_ima: {
      'Floresta Nebular de Crista / Serra Geral': 'Matas de altitude e bordas dos cânions da Serra Geral.',
      'Floresta Tropical Meridional / Encostas': 'Floresta Ombrófila Densa das encostas e vales profundos.',
      'Floresta Tropical da Planície Quaternária Sul': 'Florestas originalmente associadas às planícies do Extremo Sul.',
      'Vegetação de Influência Fluvio-Marinha': 'Restingas, banhados e formações costeiras/estuarinas.',
    },
    amesc_geomorfologia_ibge: {
      'Planalto das Araucárias': 'Escarpa e topo do Planalto Meridional (aparados e cânions).',
      'Depressão da Zona Carbonífera Catarinense': 'Relevo colinoso e morros interiores da bacia sedimentar.',
      'Formas Agradacionais Atuais e Subatuais Interioranas': 'Terraços e planícies aluviais dos rios da bacia do Araranguá.',
      'Planícies Costeiras': 'Cordões arenosos, terraços marinhos e lagoas costeiras.',
      'Planícies Deltáicas, Estuarinas e Praiais': 'Faixa litorânea de Balneário Arroio do Silva, Gaivota e Passo de Torres.',
      "Corpo d'água continental": 'Grandes lagoas e espelhos d’água.',
    },
    amesc_pedologia_ibge: {
      CAMBISSOLO: 'Solos pouco desenvolvidos de encostas e morros (atenção à erosão).',
      GLEISSOLO: 'Solos hidromórficos de várzeas alagáveis (principal base da rizicultura).',
      ARGISSOLO: 'Solos bem desenvolvidos de colinas e terraços agrícolas.',
      NEOSSOLO: 'Solos jovens: Litólicos nas escarpas e Quartzarênicos nas dunas/praias.',
      ESPODOSSOLO: 'Solos arenosos de restingas e cordões litorâneos antigos.',
      ORGANOSSOLO: 'Solos turfosos ricos em matéria orgânica em banhados.',
      NITOSSOLO: 'Solos argilosos profundos e férteis derivados de rochas basálticas.',
    },
    amesc_rodovias_osm: {
      'Federal (DNIT)': 'Rodovias federais BR-101 e BR-285.',
      'Estadual (SIE-SC)': 'Rodovias estaduais catarinenses (SC-108, SC-285, SC-290, SC-447, SC-448, SC-449).',
      'Rodovia / Acesso Regional': 'Eixos arteriais e acessos intermunicipais.',
    },
    amesc_sistema_viario_osm: {
      'Via Local / Urbana': 'Ruas e avenidas urbanas das cidades e balneários da AMESC.',
      'Estrada Municipal / Vicinal': 'Estradas municipais de ligação entre comunidades e sedes.',
      'Estrada Rural / Agrícola': 'Caminhos rurais, acessos a lavouras e propriedades.',
    },
    amesc_saude_cnes: {
      'Pública Municipal': 'UBSs, ESFs, Policlínicas e CAPS das Secretarias Municipais de Saúde.',
      'Pública Estadual/Federal': 'Unidades públicas estaduais ou federais.',
      'Sem Fins Lucrativos': 'Hospitais filantrópicos e entidades conveniadas ao SUS.',
      'Privada / Empresarial': 'Clínicas, consultórios, laboratórios e serviços privados ativos no CNES.',
    },
    amesc_licenciamento_ima: {
      LICENCIAMENTO: 'Processos de Licenciamento Ambiental (LAP, LAI, LAO, AuA) no Sinfat/IMA-SC.',
      EXPLORACAO_FLORESTAL: 'Autorizações de Corte e Manejo Florestal no Sinfat.',
      CERTIDAO_DECLARACAO: 'Certidões de Conformidade e Declarações de Atividade Não Constante.',
    },
  };

  const FIELD_LABELS = [
    ['nome_camada', 'Nome da Camada'],
    ['descricao', 'Descrição'],
    ['categoria', 'Grupo Temático'],
    ['orgao_responsavel', 'Órgão Responsável'],
    ['instituicao_fornecedora', 'Instituição Fornecedora'],
    ['url_fonte_original', 'URL da Fonte Original'],
    ['url_download_ou_servico', 'URL de Download / Serviço'],
    ['formato', 'Formato'],
    ['tipo_geometria', 'Tipo de Geometria'],
    ['sistema_referencia_coordenadas', 'Sistema de Referência (SRC)'],
    ['escala_cartografica', 'Escala Cartográfica'],
    ['resolucao_espacial', 'Resolução Espacial'],
    ['data_producao', 'Data de Produção'],
    ['data_atualizacao', 'Última Atualização'],
    ['data_consulta', 'Data de Consulta'],
    ['abrangencia_territorial', 'Abrangência Territorial'],
    ['licenca_uso', 'Licença de Uso'],
    ['restricoes_acesso', 'Restrições de Acesso'],
    ['metodo_obtencao', 'Método de Obtenção'],
    ['observacoes_qualidade', 'Qualidade / Validação'],
    ['status_validacao', 'Status'],
  ];

  function getSourceBadgeMeta(sourceClass) {
    if (sourceClass === 'Científica') return { cls: 'src-cientifica', label: 'Científica', title: 'Base técnica/científica de alta resolução (FBDS)' };
    if (sourceClass === 'Colaborativa') return { cls: 'src-colaborativa', label: 'Colaborativa (OSM)', title: 'Mapeamento colaborativo aberto OpenStreetMap (ODbL)' };
    return { cls: 'src-oficial', label: 'Oficial', title: 'Dado oficial produzido por órgão público (IBGE, IMA-SC, SGB/CPRM, DNIT, IPHAN, INCRA, ANEEL, DataSUS)' };
  }

  function getEntry(layerId, fallbackCfg = {}) {
    const isOsm = layerId.includes('osm');
    const isFbds = layerId.includes('fbds');
    const isIma = layerId.includes('_ima') || layerId.includes('ucs_mma');
    const isSigsc = layerId.includes('sigsc');
    const isDnit = layerId.includes('dnit');
    const isIphan = layerId.includes('iphan');
    const isIncra = layerId.includes('incra');
    const isAneel = layerId.includes('aneel');
    const isCnes = layerId.includes('cnes');
    const isSgb = layerId.includes('sgb') || layerId.includes('siagas');
    const org = isOsm ? 'OpenStreetMap (colaborativo)'
      : isFbds ? 'FBDS — Fundação Brasileira para o Desenvolvimento Sustentável'
      : isIma ? 'IMA-SC / MMA-ICMBio'
      : isSigsc ? 'Governo de SC — SDS / SIGSC'
      : isDnit ? 'DNIT — Departamento Nacional de Infraestrutura de Transportes'
      : isIphan ? 'IPHAN / CNSA (via DNITGeo)'
      : isIncra ? 'INCRA — SIGEF (Parcelas Certificadas)'
      : isAneel ? 'ANEEL — SIGEL'
      : isCnes ? 'Ministério da Saúde / DataSUS (CNES)'
      : isSgb ? 'SGB / CPRM — Serviço Geológico do Brasil'
      : 'IBGE — Instituto Brasileiro de Geografia e Estatística';
    const url = isOsm ? 'https://www.openstreetmap.org/'
      : isFbds ? 'https://geo.fbds.org.br/SC/'
      : isIma ? 'https://geo.ima.sc.gov.br/'
      : isSigsc ? 'https://sigsc.sc.gov.br/'
      : isDnit || isIphan ? 'https://servicos.dnit.gov.br/dnitgeo/'
      : isIncra ? 'https://geoportal.incra.gov.br/'
      : isAneel ? 'https://sigel.aneel.gov.br/'
      : isCnes ? 'https://apidadosabertos.saude.gov.br/'
      : isSgb ? 'https://geoservicos.sgb.gov.br/'
      : 'https://www.ibge.gov.br/';
    return makeMeta({
      sourceClass: isOsm ? 'Colaborativa' : (isFbds ? 'Científica' : 'Oficial'),
      nome_camada: fallbackCfg.name || layerId,
      whatIsThis: fallbackCfg.description || fallbackCfg.name || layerId,
      categoria: fallbackCfg.groupName || fallbackCfg.group || 'Geoinformação Regional AMESC',
      orgao_responsavel: org,
      url_fonte_original: url,
      formato: fallbackCfg.type === 'wms' ? 'Serviço WMS HTTPS' : (fallbackCfg.type === 'xyz' ? 'Tiles XYZ' : 'GeoJSON (SIRGAS 2000 / WGS84)'),
      tipo_geometria: fallbackCfg.geomType === 'point' ? 'Ponto' : (fallbackCfg.geomType === 'line' ? 'Linha' : (fallbackCfg.type === 'wms' || fallbackCfg.type === 'xyz' ? 'Raster / Imagem' : 'Polígono')),
      escala_cartografica: isFbds ? '1:5.000' : (layerId.includes('bdia') || layerId.includes('ibge') ? '1:250.000 / Variável' : '1:25.000 / 1:50.000'),
      redistributable: fallbackCfg.type !== 'wms' && fallbackCfg.type !== 'xyz',
    });
  }

  function getClassHelp(layerId, label) {
    const map = CLASS_HELP_MAP[layerId] || {};
    if (map[label]) return map[label];
    const low = String(label || '').toLowerCase();
    for (const [k, v] of Object.entries(map)) {
      if (k.toLowerCase() === low) return v;
    }
    return '';
  }

  return {
    FIELD_LABELS,
    CLASS_HELP_MAP,
    makeMeta,
    getEntry,
    getClassHelp,
    getSourceBadgeMeta,
  };
})();
