from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import column_property, deferred
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func

from geoalchemy2 import Geometry
from .database import session

import json

Base = declarative_base()
Base.query = session.query_property()


class MapMixin:
    @declared_attr
    def __tablename__(cls):
        return "planet_osm_" + cls.__name__.lower()

    src_id = Column("osm_id", Integer, primary_key=True, autoincrement=False)
    name = Column(String)

    tags = Column(postgresql.HSTORE)

    @declared_attr
    def way(cls):
        return deferred(
            Column(Geometry("GEOMETRY", srid=4326, spatial_index=True), nullable=False)
        )

    @declared_attr
    def kml(cls):
        return column_property(func.ST_AsKML(cls.way), deferred=True)

    @declared_attr
    def geojson_str(cls):
        return column_property(func.ST_AsGeoJSON(cls.way), deferred=True)

    def geojson(self):
        return json.loads(self.geojson_str)

    @classmethod
    def coords_within(cls, lat, lon):
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        return cls.query.filter(
            cls.admin_level.isnot(None), func.ST_Within(point, cls.way)
        ).order_by(cls.area)

    @property
    def id(self):
        return abs(self.src_id)  # relations have negative IDs

    @property
    def identifier(self):
        return f"{self.type}/{self.id}"

    @property
    def osm_url(self):
        return f"https://www.openstreetmap.org/{self.type}/{self.id}"


class Point(MapMixin, Base):
    type = "node"


class Line(MapMixin, Base):
    @property
    def type(self):
        return "way" if self.src_id > 0 else "relation"


class Polygon(MapMixin, Base):
    @property
    def type(self):
        return "way" if self.src_id > 0 else "relation"

    @declared_attr
    def area(cls):
        return column_property(func.ST_Area(cls.way, False), deferred=True)

    @hybrid_property
    def area_in_sq_km(self):
        return self.area / (1000 * 1000)
