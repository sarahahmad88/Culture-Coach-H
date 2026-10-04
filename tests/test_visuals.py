"""Verify chart evidence gates and safe persona rendering."""
import unittest
from unittest.mock import patch
from schemas import Scorecard,DimensionScore
from ui import visuals
from tests.test_core import started

class VisualTests(unittest.TestCase):
    def card(self):
        return Scorecard(overall=50,coverage=.5,dimensions=[DimensionScore(dimension='Available',value=2.5,status='scored',explanation='Evidence'),DimensionScore(dimension='Missing',value=None,status='insufficient_evidence',explanation='Missing')])
    def test_demo_never_plots_performance(self):
        with patch.object(visuals.st,'plotly_chart') as plot,patch.object(visuals.st,'info'):
            visuals.dimension_chart(self.card(),'demo','test');plot.assert_not_called()
    def test_missing_values_are_not_zero(self):
        with patch.object(visuals.st,'plotly_chart') as plot,patch.object(visuals.st,'dataframe'):
            visuals.dimension_chart(self.card(),'live','test')
            fig=plot.call_args.args[0]
            self.assertEqual(list(fig.data[0].x),[2.5]);self.assertEqual(list(fig.data[0].y),['Available'])
    def test_trend_order_and_scale(self):
        a,_=started();b=a.model_copy(deep=True)
        a.created_at='2026-10-01';b.created_at='2026-10-02'
        a.scorecard=self.card();b.scorecard=self.card();b.scorecard.overall=60
        with patch.object(visuals.st,'plotly_chart') as plot:
            visuals.trend_chart([b,a],'test');fig=plot.call_args.args[0]
            self.assertEqual(list(fig.data[0].y),[50,60]);self.assertEqual(list(fig.layout.yaxis.range),[0,100])
    def test_persona_escaping_and_motion_off(self):
        html=visuals.persona_html('<script>alert(1)</script>','<img onerror="x">','ready',motion=False)
        self.assertNotIn('<script>',html);self.assertNotIn('<img',html);self.assertIn('&lt;script&gt;',html);self.assertNotIn('learner motion',html)
    def test_empty_activity_does_not_invent_records(self):
        with patch.object(visuals.st,'altair_chart') as plot,patch.object(visuals.st,'info'):
            visuals.activity_chart([]);plot.assert_not_called()
    def test_demo_filter_hides_live_trend(self):
        from streamlit.testing.v1 import AppTest
        from pathlib import Path
        a,c=started()
        for i in range(3):c.submit(a,'A practical suggestion '+str(i),str(i))
        a.mode='live';a.scorecard=self.card()
        b=a.model_copy(deep=True,update={'id':'comparison-attempt','created_at':'2026-10-05'})
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run()
        at.session_state['repo'].save(a,True);at.session_state['repo'].save(b,True)
        at.radio[0].set_value('Progress').run();self.assertFalse(list(at.exception));self.assertEqual(len(at.get('plotly_chart')),1)
        next(x for x in at.selectbox if x.label=='Filter by mode').select('demo').run()
        self.assertFalse(list(at.exception));self.assertEqual(len(at.get('plotly_chart')),0)
