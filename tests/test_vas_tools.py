"""Synthetic fixtures test mechanics only; they are not VAS predictions or research results."""
import copy
import io
import json
import math
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/vas-scanning/scripts'
sys.path.insert(0, str(SCRIPTS))
import native_io as nio
import vas
from vas_metrics import measure_r


class VASToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def create_report(self, black_heat=False):
        source = Image.new('RGB', (200, 200), 'black')
        heat = Image.new('RGB', source.size, 'black' if black_heat else 'red')
        regions = source.copy()
        draw = ImageDraw.Draw(regions)
        draw.ellipse((65,65,155,155), outline='yellow', width=2)
        draw.rectangle((135,35,179,54), fill='white', outline='yellow', width=2)
        draw.text((139,38), '64%', fill='black')
        sequence = source.copy()
        draw = ImageDraw.Draw(sequence)
        for order, (x,y) in enumerate([(70,160),(80,175),(100,160),(110,175)], 1):
            draw.ellipse((x-12,y-12,x+12,y+12), fill='white', outline='red', width=2)
            draw.text((x-3,y-5), str(order), fill='red')
        legend_array = np.zeros((10,100,3), dtype='uint8')
        legend_array[:,:,0] = np.linspace(0,255,100).astype('uint8')
        legend_array[:,:,2] = np.linspace(255,0,100).astype('uint8')
        assets = {'_VAS_Original': source, '_VAS_Heatmap': heat, '_VAS_Regions': regions,
                  '_VAS_VisualSequence': sequence, '_Results_Legend': Image.fromarray(legend_array)}
        report = self.root / 'report.zip'
        with zipfile.ZipFile(report, 'w') as archive:
            for suffix, image in assets.items():
                buffer = io.BytesIO(); image.save(buffer, format='PNG')
                archive.writestr('SyntheticOnly' + suffix + '.png', buffer.getvalue())
        return report

    def create_case(self, black_heat=False):
        case = self.root/'case'
        manifest = nio.prepare(self.create_report(black_heat), case)
        contour = [[110+45*math.cos(t),110+45*math.sin(t)] for t in np.linspace(0,2*math.pi,150,endpoint=False)]
        review = {'report_sha256':manifest['report_sha256'],'native_size':[200,200],
                  'native_verified':True,'evidence':'Synthetic test fixture geometry only; not measured attention.',
                  'layout':'single','panels':[{'id':'scene','box':[0,0,200,200]}],
                  'hotspots_complete':True,'hotspots':[{'source_box':[135,35,45,20],
                  'panel_index':0,'hotspot_anchor':[145,82],'native_contour':contour,'probability':64}],
                  'gaze':[{'order':i,'x':x,'y':y} for i,(x,y) in enumerate([(70,160),(80,175),(100,160),(110,175)],1)],
                  'regions':[{'id':'synthetic-scene','roi':[[0,0],[199,0],[199,199],[0,199]],
                  'aoi':{'box':[0,0,200,200],'probability':80,'evidence':'Synthetic scalar for an arithmetic test.'}}],
                  'legend':{'box':[0,0,100,10],'range':[1,99],'evidence':'Known synthetic test gradient.'}}
        (case/'review.json').write_text(json.dumps(review),encoding='utf-8')
        return case, review

    def save_review(self, case, review):
        (case/'review.json').write_text(json.dumps(review),encoding='utf-8')

    def test_default_render_does_not_compute_or_require_metrics(self):
        case, review = self.create_case()
        review['regions'] = []; review['legend'] = None
        self.save_review(case, review)
        with patch('vas_metrics.calculate', side_effect=AssertionError('Metrics must not run')):
            result = vas.render(case, width=200)
        self.assertEqual(result['metrics_computed'], [])
        self.assertEqual(result['display_heatmap_weight'], .45)
        self.assertFalse(list(case.glob('metrics*.json')))
        self.assertEqual(result['state'], 'needs_visual_review')

    def test_native_probability_pixels_are_copied_without_number_redrawing(self):
        case, _ = self.create_case()
        result = vas.render(case, width=200)
        with Image.open(result['output_file']) as output, Image.open(case/'native/Regions.png') as native:
            placement = result['probability_label_placements'][0]
            self.assertEqual(output.crop(tuple(placement['destination_box'])).tobytes(), native.crop((135,35,180,55)).tobytes())

    def test_r_and_c_opt_in_math_and_sensitivity(self):
        case, _ = self.create_case()
        result = vas.metrics(case, 'both')
        self.assertAlmostEqual(result['R'][0]['primary']['R'], 50)
        self.assertEqual(len(result['R'][0]['sensitivity']), 72)
        row = result['C'][0]
        self.assertEqual([row[k] for k in ['H_approx','P','G','A']], [100,64,100,80])
        self.assertEqual(row['C_exploratory'], 86)
        self.assertFalse(result['official_3m_score'])

    def test_display_weight_cannot_change_metrics(self):
        case, _ = self.create_case()
        before = vas.metrics(case, 'r', output=self.root/'before.json')
        vas.render(case, weight=.2, width=200, output=self.root/'light.png')
        vas.render(case, weight=.8, width=200, output=self.root/'strong.png')
        after = vas.metrics(case, 'r', output=self.root/'after.json')
        self.assertEqual(before, after)

    def test_empty_heatmap_r_is_null_not_a_fabricated_zero(self):
        case, _ = self.create_case(black_heat=True)
        self.assertIsNone(vas.metrics(case,'r')['R'][0]['primary']['R'])

    def test_native_review_is_required(self):
        case, review = self.create_case(); review['native_verified'] = False
        self.save_review(case,review)
        with self.assertRaisesRegex(ValueError,'Visually review'):
            vas.render(case,width=200)

    def test_report_and_asset_tampering_are_rejected(self):
        case, _ = self.create_case(); path=case/'native/Heatmap.png'; path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'Native asset changed'):
            vas.render(case,width=200)

    def test_wrong_review_report_hash_rejected(self):
        case, review = self.create_case(); review['report_sha256']='0'*64; self.save_review(case,review)
        with self.assertRaisesRegex(ValueError,'does not match'):
            vas.metrics(case,'r')

    def test_roi_missing_rejected_only_for_calculation(self):
        case, review = self.create_case(); review['regions']=[]; self.save_review(case,review)
        vas.render(case,width=200)
        with self.assertRaisesRegex(ValueError,'regions'):
            vas.metrics(case,'r')

    def test_c_rejects_missing_aoi(self):
        case, review = self.create_case(); review['regions'][0].pop('aoi'); self.save_review(case,review)
        with self.assertRaisesRegex(ValueError,'AOI probability'):
            vas.metrics(case,'c')

    def test_c_rejects_missing_legend(self):
        case, review = self.create_case(); review['legend']=None; self.save_review(case,review)
        with self.assertRaisesRegex(ValueError,'legend'):
            vas.metrics(case,'c')

    def test_c_rejects_unknown_hotspot_value(self):
        case, review = self.create_case(); review['hotspots'][0]['probability']=None; self.save_review(case,review)
        with self.assertRaisesRegex(ValueError,'hotspot probability'):
            vas.metrics(case,'c')

    def test_missing_gaze_not_filled(self):
        case, review = self.create_case(); review['gaze'].pop(); self.save_review(case,review)
        with self.assertRaisesRegex(ValueError,'four unique'):
            vas.render(case,width=200)

    def test_montage_requires_actual_panels(self):
        case, review = self.create_case(); review['layout']='montage'; self.save_review(case,review)
        with self.assertRaisesRegex(ValueError,'panel bounds'):
            vas.render(case,width=200)

    def test_label_anchor_cannot_cross_panels(self):
        case, review = self.create_case(); review['panels'][0]['box']=[0,0,100,200]; self.save_review(case,review)
        with self.assertRaisesRegex(ValueError,'mapped panel'):
            vas.render(case,width=200)

    def test_existing_figure_is_not_overwritten(self):
        case, _ = self.create_case(); vas.render(case,width=200)
        with self.assertRaises(FileExistsError):
            vas.render(case,weight=.9,width=200)

    def test_identical_render_is_idempotent(self):
        case, _ = self.create_case()
        self.assertEqual(vas.render(case,width=200),vas.render(case,width=200))

    def test_approve_binds_visual_evidence_to_exact_output(self):
        case, _ = self.create_case(); result=vas.render(case,width=200)
        verification=vas.approve(case,case/'figure.composition.json','Synthetic comparison inspected for test purposes.')
        self.assertTrue(verification['visual_QA_passed'])
        self.assertEqual(verification['output_sha256'],result['output_sha256'])
        Path(result['output_file']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed'):
            vas.approve(case,case/'figure.composition.json','Second check')

    def test_cli_metrics_requires_an_explicit_choice(self):
        case, _ = self.create_case()
        process=subprocess.run([sys.executable,str(SCRIPTS/'vas.py'),'metrics','--case',str(case)],capture_output=True)
        self.assertEqual(process.returncode,2)
        self.assertFalse(list(case.glob('metrics*.json')))

    def test_prepare_does_not_overwrite_case(self):
        case, _ = self.create_case()
        with self.assertRaises(FileExistsError):
            nio.prepare(self.root/'report.zip',case)

    def test_unsafe_zip_paths_symlinks_and_duplicate_basenames(self):
        bad_cases=[['../evil.png'],['C:/evil.png'],['a/duplicate.png','b/duplicate.png']]
        for index,names in enumerate(bad_cases):
            path=self.root/f'bad-{index}.zip'
            with zipfile.ZipFile(path,'w') as z:
                for name in names:z.writestr(name,b'not read')
            with self.assertRaises(ValueError):nio.parse_report(path)
        path=self.root/'symlink.zip'
        with zipfile.ZipFile(path,'w') as z:
            info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(info,'target')
        with self.assertRaises(ValueError):nio.parse_report(path)

    def test_zip_expanded_size_is_bounded(self):
        class Huge:
            file_size=100_000_001
        class FakeArchive:
            def infolist(self):return [Huge()]
        with self.assertRaisesRegex(ValueError,'limit'):
            nio.safe_members(FakeArchive())


if __name__ == '__main__':
    unittest.main()
