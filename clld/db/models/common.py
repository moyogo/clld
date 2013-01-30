from itertools import groupby

from sqlalchemy import (
    Column,
    Float,
    Integer,
    String,
    Boolean,
    Unicode,
    Date,
    LargeBinary,
    CheckConstraint,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import (
    relationship,
    validates,
    backref,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.associationproxy import association_proxy

from zope.interface import implementer

from clld.db.meta import Base, PolymorphicBaseMixin
from clld.db.versioned import Versioned
from clld import interfaces


#
# TODO: relations to data and files!
#
"""
http://chart.googleapis.com/chart?cht=p&chs=38x38&chd=t:60,40&chco=FF0000|00FF00&chf=bg,s,FFFFFF00

note: deprecated; only works until april 2015!

chs: 38px charts result in the pie having a diameter of about 17px
chd: series of numbers
chco: colors per slice
chf: make sure backgroud is transparent (the 00 added to the color spec)
"""


#-----------------------------------------------------------------------------
# We augment mapper classes for basic objects using mixins to add the ability
# to store arbitrary key-value pairs and files associated with an object.
#-----------------------------------------------------------------------------
class File(Base):
    """Model for storage of files in the database.
    """
    name = Column(Unicode)
    mime_type = Column(String)
    content = Column(LargeBinary)


class FilesMixin(object):
    """This mixin provides a way to associate files with another model class.
    """
    @classmethod
    def owner_class(cls):
        return cls.__name__.split('_')[0]

    name = Column(Unicode)
    ord = Column(Integer, default=1)

    @declared_attr
    def file_pk(cls):
        return Column(Integer, ForeignKey('file.pk'))

    @declared_attr
    def file(cls):
        return relationship(File)

    @declared_attr
    def object_pk(cls):
        return Column(Integer, ForeignKey('%s.pk' % cls.owner_class().lower()))

    #@declared_attr
    #def object(cls):
    #    return relationship(cls.owner_class(), backref=backref('files', order_by=cls.ord))


class HasFilesMixin(object):
    """Adds a convenience method to retrieve a dict of associated files.

    .. note::

        It is the responsibility of the programmer to make sure conversion to a dict makes
        sense, i.e. the names of associated files are actually unique.
    """
    def filesdict(self):
        return dict((f.name, f.file) for f in self.files)

    @declared_attr
    def data(cls):
        return relationship(cls.__name__ + '_files')


class DataMixin(object):
    """This mixin provides a simple way to attach arbitrary key-value pairs to another
    model class identified by class name.
    """
    @classmethod
    def owner_class(cls):
        return cls.__name__.split('_')[0]

    key = Column(Unicode)
    value = Column(Unicode)
    ord = Column(Integer, default=1)

    @declared_attr
    def object_pk(cls):
        return Column(Integer, ForeignKey('%s.pk' % cls.owner_class().lower()))

    #@declared_attr
    #def object(cls):
    #    return relationship(cls.owner_class(), backref=backref('data', order_by=cls.ord))


class HasDataMixin(object):
    """Adds a convenience method to retrieve the key-value pairs from data as dict.

    .. note::

        It is the responsibility of the programmer to make sure conversion to a dict makes
        sense, i.e. the keys in data are actually unique.
    """
    def datadict(self):
        return dict((d.key, d.value) for d in self.data)

    @declared_attr
    def data(cls):
        return relationship(cls.__name__ + '_data')


class IdNameDescriptionMixin(object):
    """id is to be used as string identifier which can be used for sorting and as
    URL part.
    """
    id = Column(String, unique=True)
    name = Column(Unicode)
    description = Column(Unicode)


#-----------------------------------------------------------------------------
# The mapper classes for basic objects of the clld db model are marked as
# implementers of the related interface.
#-----------------------------------------------------------------------------
class Language_data(Base, Versioned, DataMixin):
    pass


class Language_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.ILanguage)
class Language(Base,
               PolymorphicBaseMixin,
               Versioned,
               IdNameDescriptionMixin,
               HasDataMixin,
               HasFilesMixin):
    """Languages are the main objects of discourse. We attach a geo-coordinate
    to them to be able to put them on maps.
    """
    __table_args__ = (UniqueConstraint('name'),)
    latitude = Column(Float(), CheckConstraint('-90 <= latitude and latitude <= 90'))
    longitude = Column(Float(), CheckConstraint('-180 <= longitude and longitude <= 180 '))
    identifiers = association_proxy('languageidentifier', 'identifier')


class DomainElement_data(Base, Versioned, DataMixin):
    pass


class DomainElement_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.IDomainElement)
class DomainElement(Base,
                    PolymorphicBaseMixin,
                    Versioned,
                    IdNameDescriptionMixin,
                    HasDataMixin,
                    HasFilesMixin):
    __table_args__ = (UniqueConstraint('name', 'parameter_pk'),)

    parameter_pk = Column(Integer, ForeignKey('parameter.pk'))

    # do we need a numeric value for these?


class Parameter_data(Base, Versioned, DataMixin):
    pass


class Parameter_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.IParameter)
class Parameter(Base,
                PolymorphicBaseMixin,
                Versioned,
                IdNameDescriptionMixin,
                HasDataMixin,
                HasFilesMixin):
    __table_args__ = (UniqueConstraint('name'),)
    domain = relationship('DomainElement', backref='parameter', order_by=DomainElement.id)

    @property
    def languages(self):
        for language, values in groupby(self.values, lambda v: v.language):
            yield language


class Source_data(Base, Versioned, DataMixin):
    pass


class Source_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.ISource)
class Source(Base,
             PolymorphicBaseMixin,
             Versioned,
             IdNameDescriptionMixin,
             HasDataMixin,
             HasFilesMixin):
    glottolog_id = Column(String)
    google_book_search_id = Column(String)


class Contribution_data(Base, Versioned, DataMixin):
    pass


class Contribution_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.IContribution)
class Contribution(Base,
                   PolymorphicBaseMixin,
                   Versioned,
                   IdNameDescriptionMixin,
                   HasDataMixin,
                   HasFilesMixin):
    __table_args__ = (UniqueConstraint('name'),)
    date = Column(Date)

    @property
    def primary_contributors(self):
        return [assoc.contributor for assoc in
                sorted(self.contributor_assocs, key=lambda a: a.ord) if assoc.primary]

    @property
    def secondary_contributors(self):
        return [assoc.contributor for assoc in
                sorted(self.contributor_assocs, key=lambda a: a.ord) if not assoc.primary]


class Value_data(Base, Versioned, DataMixin):
    pass


class Value_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.IValue)
class Value(Base,
            PolymorphicBaseMixin,
            Versioned,
            IdNameDescriptionMixin,
            HasDataMixin,
            HasFilesMixin):
    language_pk = Column(Integer, ForeignKey('language.pk'))
    parameter_pk = Column(Integer, ForeignKey('parameter.pk'))
    contribution_pk = Column(Integer, ForeignKey('contribution.pk'))

    # Values may be taken from a domain.
    domainelement_pk = Column(Integer, ForeignKey('domainelement.pk'))

    # Languages may have multiple values for the same parameter. Their relative
    # frequency can be stored here.
    frequency = Column(Float)

    parameter = relationship('Parameter', backref='values')
    domainelement = relationship('DomainElement', backref='values')
    contribution = relationship('Contribution', backref='values')

    @declared_attr
    def language(cls):
        return relationship('Language', backref=backref('values', order_by=cls.language_pk))

    @validates('parameter_pk')
    def validate_parameter_pk(self, key, parameter_pk):
        """We have to make sure, the parameter a value is tied to and the parameter a
        possible domainelement is tied to stay in sync.
        """
        if self.domainelement:
            assert self.domainelement.parameter_pk == parameter_pk
        return parameter_pk


class Contributor_data(Base, Versioned, DataMixin):
    pass


class Contributor_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.IContributor)
class Contributor(Base,
                  PolymorphicBaseMixin,
                  Versioned,
                  IdNameDescriptionMixin,
                  HasDataMixin,
                  HasFilesMixin):
    __table_args__ = (UniqueConstraint('name'),)
    url = Column(Unicode())
    email = Column(String)
    address = Column(Unicode)


class Sentence_data(Base, Versioned, DataMixin):
    pass


class Sentence_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.ISentence)
class Sentence(Base,
               PolymorphicBaseMixin,
               Versioned,
               HasDataMixin,
               HasFilesMixin):
    pass


class Unit_data(Base, Versioned, DataMixin):
    pass


class Unit_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.IUnit)
class Unit(Base,
           PolymorphicBaseMixin,
           Versioned,
           IdNameDescriptionMixin,
           HasDataMixin,
           HasFilesMixin):
    language_pk = Column(Integer, ForeignKey('language.pk'))
    language = relationship(Language)


class UnitDomainElement_data(Base, Versioned, DataMixin):
    pass


class UnitDomainElement_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.IUnitDomainElement)
class UnitDomainElement(Base,
                        PolymorphicBaseMixin,
                        Versioned,
                        IdNameDescriptionMixin,
                        HasDataMixin,
                        HasFilesMixin):
    unitparameter_pk = Column(Integer, ForeignKey('unitparameter.pk'))
    ord = Column(Integer)

    # do we need a numeric value for these?


class UnitParameter_data(Base, Versioned, DataMixin):
    pass


class UnitParameter_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.IUnitParameter)
class UnitParameter(Base,
                    PolymorphicBaseMixin,
                    Versioned,
                    IdNameDescriptionMixin,
                    HasDataMixin,
                    HasFilesMixin):
    domain = relationship('UnitDomainElement', backref='parameter', order_by=UnitDomainElement.id)


class UnitValue_data(Base, Versioned, DataMixin):
    pass


class UnitValue_files(Base, Versioned, FilesMixin):
    pass


@implementer(interfaces.IUnitValue)
class UnitValue(Base,
                PolymorphicBaseMixin,
                Versioned,
                IdNameDescriptionMixin,
                HasDataMixin,
                HasFilesMixin):
    unit_pk = Column(Integer, ForeignKey('unit.pk'))
    unitparameter_pk = Column(Integer, ForeignKey('unitparameter.pk'))
    contribution_pk = Column(Integer, ForeignKey('contribution.pk'))

    # Values may be taken from a domain.
    unitdomainelement_pk = Column(Integer, ForeignKey('unitdomainelement.pk'))

    # Languages may have multiple values for the same parameter. Their relative
    # frequency can be stored here.
    frequency = Column(Float)

    unitparameter = relationship('UnitParameter', backref='unitvalues')
    unitdomainelement = relationship('UnitDomainElement', backref='unitvalues')
    contribution = relationship('Contribution', backref='unitvalues')

    @declared_attr
    def unit(cls):
        return relationship('Unit', backref=backref('unitvalues', order_by=cls.unit_pk))

    @validates('parameter_pk')
    def validate_parameter_pk(self, key, unitparameter_pk):
        """We have to make sure, the parameter a value is tied to and the parameter a
        possible domainelement is tied to stay in sync.
        """
        if self.unitdomainelement:
            assert self.unitdomainelement.unitparameter_pk == unitparameter_pk
        return unitparameter_pk


#-----------------------------------------------------------------------------
# Non-core mappers and association tables
#-----------------------------------------------------------------------------
class Identifier(Base, Versioned, IdNameDescriptionMixin):
    """We want to be able to link languages to languages in other systems. Thus,
    we store identifiers of various types like 'wals', 'iso639-3', 'glottolog'.
    """
    __table_args__ = (UniqueConstraint('name', 'type'), UniqueConstraint('id'))
    type = Column(String)

    @validates('type')
    def validate_type(self, key, type):
        assert type in ['wals', 'iso639-3', 'glottolog']
        return type

    def url(self):
        """
        :return: canonical URL for a language identifier
        """
        #
        # TODO!
        #
        if self.type == 'wals':
            return 'http://wals.info/...'


class LanguageIdentifier(Base, Versioned):
    """Languages are linked to identifiers with an optional description of this
    linkage, e.g. 'is dialect of'.
    """
    language_pk = Column(Integer, ForeignKey('language.pk'))
    identifier_pk = Column(Integer, ForeignKey('identifier.pk'))
    description = Column(Unicode)

    identifier = relationship(Identifier)
    language = relationship(
        Language,
        backref=backref("languageidentifier", cascade="all, delete-orphan"))


#
# Several objects can be linked to sources, i.e. they can have references.
#
class HasSourceMixin(object):
    key = Column(Unicode)  # the citation key, specific (and unique) within a contribution
    description = Column(Unicode)  # e.g. page numbers.

    @declared_attr
    def source_pk(cls):
        return Column(Integer, ForeignKey('source.pk'))

    @declared_attr
    def source(cls):
        return relationship(Source, backref=cls.__name__.lower() + 's')


class ValueReference(Base, Versioned, HasSourceMixin):
    """Values are linked to Sources with an optional description of this
    linkage, e.g. 'pp. 30-34'.
    """
    value_pk = Column(Integer, ForeignKey('value.pk'))

    @declared_attr
    def value(cls):
        return relationship(Value, backref=backref("references", order_by=cls.key))


class SentenceReference(Base, Versioned, HasSourceMixin):
    """
    """
    sentence_pk = Column(Integer, ForeignKey('sentence.pk'))

    @declared_attr
    def sentence(cls):
        return relationship(Sentence, backref=backref("references", order_by=cls.key))


class ContributionContributor(Base, PolymorphicBaseMixin, Versioned):
    """Many-to-many association between contributors and contributions
    """
    contribution_pk = Column(Integer, ForeignKey('contribution.pk'))
    contributor_pk = Column(Integer, ForeignKey('contributor.pk'))

    # contributors are ordered.
    ord = Column(Integer, default=1)

    # we distinguish between primary and secondary (a.k.a. 'with ...') contributors.
    primary = Column(Boolean, default=True)

    contribution = relationship(Contribution, backref='contributor_assocs')
    contributor = relationship(Contributor, backref='contribution_assocs')


class ValueSentence(Base, PolymorphicBaseMixin, Versioned):
    """Many-to-many association between values and sentences given as explanation of a
    value.
    """
    value_pk = Column(Integer, ForeignKey('value.pk'))
    sentence_pk = Column(Integer, ForeignKey('sentence.pk'))
    description = Column(Unicode())


class UnitParameterUnit(Base, PolymorphicBaseMixin, Versioned, IdNameDescriptionMixin):
    unit_pk = Column(Integer, ForeignKey('unit.pk'))
    unitparameter_pk = Column(Integer, ForeignKey('unitparameter.pk'))
    unit = relationship(Unit, backref='unitparameter_assocs')
    unitparameter = relationship(UnitParameter, backref='unit_assocs')