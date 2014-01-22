from sqlalchemy.sql.expression import cast
from sqlalchemy.types import Integer

from clld.tests.util import TestWithEnv
from clld.db.models import common


class Tests(TestWithEnv):
    def test_DataTable(self):
        from clld.web.datatables.base import (
            DataTable, Col, LinkCol, DetailsRowLinkCol, LinkToMapCol, IntegerIdCol, IdCol,
            ExternalLinkCol,
        )

        class TestTable(DataTable):
            def col_defs(self):
                return [
                    Col(self, 'pk'),
                    DetailsRowLinkCol(self, 'd'),
                    LinkToMapCol(self, 'm'),
                    LinkCol(self, 'link'),
                    Col(self, 'active'),
                    Col(self, 'name', model_col=None),
                    Col(self, 'description', format=lambda i: 'x'),
                    IntegerIdCol(self, 'id'),
                    IdCol(self, 'nid',
                          get_object=lambda i: i, model_col=common.Contributor.id),
                    ExternalLinkCol(self, 'url')]

        dt = TestTable(self.env['request'], common.Contributor)
        assert unicode(dt) == 'Contributors'
        assert repr(dt) == 'Contributors'

        self.handle_dt(TestTable, common.Contributor)

        self.set_request_properties(params={
            'sSearch_0': '> 1',
            'sSearch_4': 'True',
            'sSearch_6': 'e',
            'iSortingCols': '1',
            'iSortCol_0': '0',
            'sSortDir_0': 'desc'})
        self.handle_dt(TestTable, common.Contributor)

        self.set_request_properties(params={'iSortingCols': 'x'})
        self.handle_dt(TestTable, common.Contributor)

        self.set_request_properties(params={'iSortingCols': '1', 'iSortCol_0': '7'})
        self.handle_dt(TestTable, common.Contributor)

        self.set_request_properties(params={'sSearch_7': '1'})
        self.handle_dt(TestTable, common.Contributor)

        self.set_request_properties(params={'sSearch_8': 'id'})
        self.handle_dt(TestTable, common.Contributor)

    def test_DataTable2(self):
        from clld.web.datatables.base import DataTable, Col, filter_number

        class TestCol(Col):
            def search(self, qs):
                return filter_number(cast(self.dt.model.pk, Integer), qs, type_=int)

        class TestTable(DataTable):
            def col_defs(self):
                return [Col(self, 'latitude'), TestCol(self, 'pk')]

        self.set_request_properties(params={'sSearch_0': '> 1', 'sSearch_1': '> 1'})
        self.handle_dt(TestTable, common.Language)

    def test_DataTable3(self):
        from clld.web.datatables.base import DataTable, PercentCol, Col

        class TestTable(DataTable):
            def col_defs(self):
                return [PercentCol(self, 'frequency'), Col(self, 'name', choices=['a'])]

        self.handle_dt(TestTable, common.Value)
        self.set_request_properties(params={'sSearch_0': '> 10', 'sSearch_1': 'a'})
        self.handle_dt(TestTable, common.Value)
