/**
 * Custom MapLibre GL style
 * Dark Blue Water (#0a192f) | Light Blue Land (#b8dbf5) | Golden Borders (#d4af37)
 */
window.GLOBAL_CAREER_MAP_STYLE = {
  "version": 8,
  "name": "Global Career Map - Dark Blue Water, Light Blue Land, Golden Borders",
  "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
  "sprite": "https://tiles.openfreemap.org/sprites/ofm_f384/ofm",
  "sources": {
    "openmaptiles": {
      "type": "vector",
      "url": "https://tiles.openfreemap.org/planet"
    }
  },
  "layers": [
    {
      "id": "background",
      "type": "background",
      "paint": {
        "background-color": "#b8dbf5"
      }
    },
    {
      "id": "park",
      "type": "fill",
      "source": "openmaptiles",
      "source-layer": "park",
      "paint": {
        "fill-color": "#a8d2ee",
        "fill-opacity": 0.65
      }
    },
    {
      "id": "landcover_ice",
      "type": "fill",
      "source": "openmaptiles",
      "source-layer": "landcover",
      "filter": [
        "in",
        [
          "get",
          "class"
        ],
        [
          "literal",
          [
            "ice_shelf",
            "glacier"
          ]
        ]
      ],
      "paint": {
        "fill-color": "#e2f2fc",
        "fill-opacity": 0.9
      }
    },
    {
      "id": "landcover_wood",
      "type": "fill",
      "source": "openmaptiles",
      "source-layer": "landcover",
      "filter": [
        "==",
        [
          "get",
          "class"
        ],
        "wood"
      ],
      "paint": {
        "fill-color": "#a4cee9",
        "fill-opacity": 0.55
      }
    },
    {
      "id": "landcover_grass",
      "type": "fill",
      "source": "openmaptiles",
      "source-layer": "landcover",
      "filter": [
        "in",
        [
          "get",
          "class"
        ],
        [
          "literal",
          [
            "grass",
            "scrub",
            "sand"
          ]
        ]
      ],
      "paint": {
        "fill-color": "#add3ec",
        "fill-opacity": 0.55
      }
    },
    {
      "id": "landuse_residential",
      "type": "fill",
      "source": "openmaptiles",
      "source-layer": "landuse",
      "filter": [
        "in",
        [
          "get",
          "class"
        ],
        [
          "literal",
          [
            "residential",
            "suburb"
          ]
        ]
      ],
      "paint": {
        "fill-color": "#c4e2f8",
        "fill-opacity": 0.65
      }
    },
    {
      "id": "landuse_commercial",
      "type": "fill",
      "source": "openmaptiles",
      "source-layer": "landuse",
      "filter": [
        "in",
        [
          "get",
          "class"
        ],
        [
          "literal",
          [
            "commercial",
            "industrial",
            "retail"
          ]
        ]
      ],
      "paint": {
        "fill-color": "#cae5f9",
        "fill-opacity": 0.65
      }
    },
    {
      "id": "water",
      "type": "fill",
      "source": "openmaptiles",
      "source-layer": "water",
      "paint": {
        "fill-color": "#0a192f",
        "fill-opacity": 1.0,
        "fill-outline-color": "rgba(212, 175, 55, 0.45)"
      }
    },
    {
      "id": "waterway",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "waterway",
      "paint": {
        "line-color": "#0a192f",
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          4,
          0.6,
          8,
          1.2,
          13,
          2.4,
          16,
          4.0
        ]
      }
    },
    {
      "id": "building",
      "type": "fill",
      "source": "openmaptiles",
      "source-layer": "building",
      "minzoom": 13,
      "paint": {
        "fill-color": "rgba(255, 255, 255, 0.45)",
        "fill-outline-color": "rgba(145, 190, 225, 0.75)"
      }
    },
    {
      "id": "highway_minor",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "transportation",
      "minzoom": 11,
      "filter": [
        "in",
        [
          "get",
          "class"
        ],
        [
          "literal",
          [
            "minor",
            "service",
            "track",
            "path"
          ]
        ]
      ],
      "paint": {
        "line-color": "#ffffff",
        "line-opacity": 0.75,
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          11,
          0.6,
          14,
          1.4,
          17,
          3.2
        ]
      }
    },
    {
      "id": "highway_secondary_tertiary",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "transportation",
      "minzoom": 8,
      "filter": [
        "in",
        [
          "get",
          "class"
        ],
        [
          "literal",
          [
            "secondary",
            "tertiary"
          ]
        ]
      ],
      "paint": {
        "line-color": "#ffffff",
        "line-opacity": 0.88,
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          8,
          0.8,
          11,
          1.6,
          15,
          3.6
        ]
      }
    },
    {
      "id": "highway_primary_trunk",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "transportation",
      "minzoom": 6,
      "filter": [
        "in",
        [
          "get",
          "class"
        ],
        [
          "literal",
          [
            "primary",
            "trunk"
          ]
        ]
      ],
      "paint": {
        "line-color": "#ffffff",
        "line-opacity": 0.95,
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          6,
          0.9,
          9,
          1.8,
          14,
          4.0
        ]
      }
    },
    {
      "id": "highway_motorway_casing",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "transportation",
      "minzoom": 4,
      "filter": [
        "==",
        [
          "get",
          "class"
        ],
        "motorway"
      ],
      "paint": {
        "line-color": "#caa03d",
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          4,
          1.4,
          8,
          3.0,
          14,
          6.0
        ]
      }
    },
    {
      "id": "highway_motorway_inner",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "transportation",
      "minzoom": 4,
      "filter": [
        "==",
        [
          "get",
          "class"
        ],
        "motorway"
      ],
      "paint": {
        "line-color": "#fff9e0",
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          4,
          0.8,
          8,
          1.8,
          14,
          4.0
        ]
      }
    },
    {
      "id": "boundary_country_glow",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "boundary",
      "filter": [
        "all",
        [
          "==",
          [
            "get",
            "admin_level"
          ],
          2
        ],
        [
          "!=",
          [
            "get",
            "maritime"
          ],
          1
        ]
      ],
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      },
      "paint": {
        "line-color": "#f59e0b",
        "line-opacity": 0.45,
        "line-blur": 2,
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          1,
          2.5,
          5,
          4.8,
          10,
          8.0
        ]
      }
    },
    {
      "id": "boundary_country",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "boundary",
      "filter": [
        "all",
        [
          "==",
          [
            "get",
            "admin_level"
          ],
          2
        ],
        [
          "!=",
          [
            "get",
            "maritime"
          ],
          1
        ]
      ],
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      },
      "paint": {
        "line-color": "#d4af37",
        "line-opacity": 1.0,
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          1,
          1.2,
          4,
          2.0,
          8,
          3.5,
          12,
          5.0
        ]
      }
    },
    {
      "id": "boundary_disputed",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "boundary",
      "filter": [
        "all",
        [
          "!=",
          [
            "get",
            "maritime"
          ],
          1
        ],
        [
          "==",
          [
            "get",
            "disputed"
          ],
          1
        ]
      ],
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      },
      "paint": {
        "line-color": "#eab308",
        "line-dasharray": [
          2,
          3
        ],
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          2,
          1.0,
          6,
          1.8,
          10,
          3.0
        ]
      }
    },
    {
      "id": "boundary_state_province",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "boundary",
      "minzoom": 3.5,
      "filter": [
        "all",
        [
          ">=",
          [
            "get",
            "admin_level"
          ],
          3
        ],
        [
          "<=",
          [
            "get",
            "admin_level"
          ],
          4
        ],
        [
          "!=",
          [
            "get",
            "maritime"
          ],
          1
        ],
        [
          "!=",
          [
            "get",
            "disputed"
          ],
          1
        ]
      ],
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      },
      "paint": {
        "line-color": "#dfa634",
        "line-dasharray": [
          3,
          2
        ],
        "line-opacity": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          3.5,
          0.4,
          5.0,
          0.85,
          9.0,
          1.0
        ],
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          3.5,
          0.8,
          7.0,
          1.6,
          11.0,
          2.5
        ]
      }
    },
    {
      "id": "boundary_local",
      "type": "line",
      "source": "openmaptiles",
      "source-layer": "boundary",
      "minzoom": 6.5,
      "filter": [
        "all",
        [
          ">=",
          [
            "get",
            "admin_level"
          ],
          5
        ],
        [
          "<=",
          [
            "get",
            "admin_level"
          ],
          8
        ],
        [
          "!=",
          [
            "get",
            "maritime"
          ],
          1
        ]
      ],
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      },
      "paint": {
        "line-color": "#e5be5e",
        "line-dasharray": [
          2,
          2
        ],
        "line-opacity": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          6.5,
          0.3,
          8.0,
          0.75,
          11.0,
          0.9
        ],
        "line-width": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          6.5,
          0.6,
          9.0,
          1.2,
          12.0,
          1.8
        ]
      }
    },
    {
      "id": "water_name_ocean",
      "type": "symbol",
      "source": "openmaptiles",
      "source-layer": "water_name",
      "filter": [
        "==",
        [
          "get",
          "class"
        ],
        "ocean"
      ],
      "layout": {
        "text-field": [
          "coalesce",
          [
            "get",
            "name_en"
          ],
          [
            "get",
            "name"
          ]
        ],
        "text-font": [
          "Noto Sans Italic",
          "Noto Sans Regular"
        ],
        "text-transform": "uppercase",
        "text-letter-spacing": 0.22,
        "text-max-width": 9,
        "text-size": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          0,
          10,
          2,
          12,
          5,
          16
        ]
      },
      "paint": {
        "text-color": "#f3cc68",
        "text-halo-color": "#061324",
        "text-halo-width": 2.2,
        "text-halo-blur": 1.2
      }
    },
    {
      "id": "water_name_sea_lake",
      "type": "symbol",
      "source": "openmaptiles",
      "source-layer": "water_name",
      "minzoom": 4,
      "filter": [
        "!=",
        [
          "get",
          "class"
        ],
        "ocean"
      ],
      "layout": {
        "text-field": [
          "coalesce",
          [
            "get",
            "name_en"
          ],
          [
            "get",
            "name"
          ]
        ],
        "text-font": [
          "Noto Sans Italic",
          "Noto Sans Regular"
        ],
        "text-letter-spacing": 0.08,
        "text-size": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          4,
          10,
          8,
          12,
          12,
          15
        ]
      },
      "paint": {
        "text-color": "#d8eeff",
        "text-halo-color": "#061324",
        "text-halo-width": 1.8
      }
    },
    {
      "id": "label_country",
      "type": "symbol",
      "source": "openmaptiles",
      "source-layer": "place",
      "maxzoom": 8,
      "filter": [
        "==",
        [
          "get",
          "class"
        ],
        "country"
      ],
      "layout": {
        "text-field": [
          "coalesce",
          [
            "get",
            "name_en"
          ],
          [
            "get",
            "name"
          ]
        ],
        "text-font": [
          "Noto Sans Bold",
          "Noto Sans Regular"
        ],
        "text-transform": "uppercase",
        "text-letter-spacing": 0.12,
        "text-max-width": 8,
        "text-size": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          1,
          10.5,
          4,
          13.5,
          7,
          18.0
        ]
      },
      "paint": {
        "text-color": "#06172d",
        "text-halo-color": "#ffffff",
        "text-halo-width": 2.4,
        "text-halo-blur": 1.0
      }
    },
    {
      "id": "label_state",
      "type": "symbol",
      "source": "openmaptiles",
      "source-layer": "place",
      "minzoom": 4,
      "maxzoom": 9,
      "filter": [
        "==",
        [
          "get",
          "class"
        ],
        "state"
      ],
      "layout": {
        "text-field": [
          "coalesce",
          [
            "get",
            "name_en"
          ],
          [
            "get",
            "name"
          ]
        ],
        "text-font": [
          "Noto Sans Regular"
        ],
        "text-letter-spacing": 0.06,
        "text-size": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          4,
          10,
          7,
          13,
          9,
          15
        ]
      },
      "paint": {
        "text-color": "#0c223c",
        "text-halo-color": "#ffffff",
        "text-halo-width": 2.0
      }
    },
    {
      "id": "label_city",
      "type": "symbol",
      "source": "openmaptiles",
      "source-layer": "place",
      "minzoom": 3.5,
      "filter": [
        "==",
        [
          "get",
          "class"
        ],
        "city"
      ],
      "layout": {
        "text-field": [
          "coalesce",
          [
            "get",
            "name_en"
          ],
          [
            "get",
            "name"
          ]
        ],
        "text-font": [
          "Noto Sans Bold",
          "Noto Sans Regular"
        ],
        "text-size": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          4,
          10.5,
          8,
          13.5,
          12,
          17.0
        ]
      },
      "paint": {
        "text-color": "#0a192f",
        "text-halo-color": "#ffffff",
        "text-halo-width": 2.0
      }
    },
    {
      "id": "label_town",
      "type": "symbol",
      "source": "openmaptiles",
      "source-layer": "place",
      "minzoom": 7,
      "filter": [
        "==",
        [
          "get",
          "class"
        ],
        "town"
      ],
      "layout": {
        "text-field": [
          "coalesce",
          [
            "get",
            "name_en"
          ],
          [
            "get",
            "name"
          ]
        ],
        "text-font": [
          "Noto Sans Regular"
        ],
        "text-size": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          7,
          9.5,
          10,
          12.0,
          13,
          15.0
        ]
      },
      "paint": {
        "text-color": "#152c48",
        "text-halo-color": "#ffffff",
        "text-halo-width": 1.8
      }
    },
    {
      "id": "label_village",
      "type": "symbol",
      "source": "openmaptiles",
      "source-layer": "place",
      "minzoom": 9.5,
      "filter": [
        "in",
        [
          "get",
          "class"
        ],
        [
          "literal",
          [
            "village",
            "hamlet"
          ]
        ]
      ],
      "layout": {
        "text-field": [
          "coalesce",
          [
            "get",
            "name_en"
          ],
          [
            "get",
            "name"
          ]
        ],
        "text-font": [
          "Noto Sans Regular"
        ],
        "text-size": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          9.5,
          9.0,
          12,
          11.5,
          14,
          13.5
        ]
      },
      "paint": {
        "text-color": "#203957",
        "text-halo-color": "#ffffff",
        "text-halo-width": 1.6
      }
    },
    {
      "id": "label_suburb",
      "type": "symbol",
      "source": "openmaptiles",
      "source-layer": "place",
      "minzoom": 11,
      "filter": [
        "in",
        [
          "get",
          "class"
        ],
        [
          "literal",
          [
            "suburb",
            "neighbourhood"
          ]
        ]
      ],
      "layout": {
        "text-field": [
          "coalesce",
          [
            "get",
            "name_en"
          ],
          [
            "get",
            "name"
          ]
        ],
        "text-font": [
          "Noto Sans Regular"
        ],
        "text-size": [
          "interpolate",
          [
            "linear"
          ],
          [
            "zoom"
          ],
          11,
          9.0,
          14,
          12.0
        ]
      },
      "paint": {
        "text-color": "#284260",
        "text-halo-color": "#ffffff",
        "text-halo-width": 1.5
      }
    }
  ]
};
