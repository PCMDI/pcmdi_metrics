import unittest
import pcmdi_metrics
import inspect
import os
import numpy
import json


class TestJSONs(unittest.TestCase):
    def testMerge(self):
        pth = os.path.dirname(inspect.getfile(self.__class__))
        J = pcmdi_metrics.io.base.JSONs([os.path.join(
            pth, "io", "merge.json")],
            oneVariablePerFile=False)
        axes_ids = J.getAxisIds()
        axes = J.getAxisList()
        self.assertEqual(axes_ids, ["upper", "lower", "numbers"])
        data = J()
        self.assertEqual(data.shape, (4, 5, 8))
        self.assertEqual(data[2, 3, 6], 23.6)

        merged = J(merge=["lower", "numbers"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper", "lower_numbers"])
        self.assertEqual(merged.shape, (4, 40))
        self.assertEqual(merged[2, 8], 21.)

        merged = J(merge=["numbers", "lower"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper", "numbers_lower"])
        self.assertEqual(merged.shape, (4, 40))
        self.assertEqual(merged[2, 8], 23.1)

        merged = J(merge=["upper", "lower"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper_lower", "numbers"])
        self.assertEqual(merged.shape, (20, 8))
        self.assertEqual(merged[7, 5], 12.5)

        merged = J(merge=["lower", "upper"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["lower_upper", "numbers"])
        self.assertEqual(merged.shape, (20, 8))
        self.assertEqual(merged[7, 5], 31.5)

        merged = J(merge=["upper", "numbers"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper_numbers", "lower"])
        self.assertEqual(merged.shape, (32, 5))
        self.assertEqual(merged[13, 4], 14.5)

        merged = J(merge=["numbers", "upper"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["numbers_upper", "lower"])
        self.assertEqual(merged.shape, (32, 5))
        self.assertEqual(merged[14, 4], 24.3)

        with self.assertRaises(RuntimeError) as context:
            merged = J(merge=["upper", "lower", "number"])
        self.assertTrue("You requested to merge axis is 'number' which is not valid." in str(
            context.exception))

        merged = J(merge=["upper", "lower", "numbers"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper_lower_numbers", ])
        self.assertEqual(merged.shape, (160,))
        self.assertEqual(merged[121], 30.1)

        merged = J(merge=["upper", "numbers", "lower"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper_numbers_lower", ])
        self.assertEqual(merged.shape, (160,))
        self.assertEqual(merged[121], 31.)

        merged = J(merge=["numbers", "upper", "lower"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["numbers_upper_lower", ])
        self.assertEqual(merged.shape, (160,))
        self.assertEqual(merged[121], 1.6)

        # Merge and subset in different order
        merged = J(upper=["C", "B", "D"], numbers=["4", "2", "1", "7", "3"], lower=[
                   "e", "a", "d", "c"], merge=["upper", "numbers"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper_numbers", "lower"])
        self.assertEqual(merged.shape, (15, 4))
        self.assertEqual(merged[9, 2], 13.2)

        merged = J(upper=["C", "B", "D"], numbers=["4", "2", "1", "7", "3"], lower=[
                   "e", "a", "d", "c"], merge=["numbers", "upper"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["numbers_upper", "lower"])
        self.assertEqual(merged.shape, (15, 4))
        self.assertEqual(merged[9, 2], 23.6)

        merged = J(upper=["C", "B", "D"], numbers=["4", "2", "1", "7", "3"], lower=[
                   "e", "a", "d", "c"], merge=["lower", "upper"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["lower_upper", "numbers"])
        self.assertEqual(merged.shape, (12, 5))
        self.assertEqual(merged[9, 2], 22.)

        merged = J(upper=["C", "B", "D"], numbers=["4", "2", "1", "7", "3"], lower=[
                   "e", "a", "d", "c"], merge=["upper", "lower"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper_lower", "numbers"])
        self.assertEqual(merged.shape, (12, 5))
        self.assertEqual(merged[9, 2], 30.)

        merged = J(upper=["C", "B", "D"], numbers=["4", "2", "1", "7", "3"], lower=[
                   "e", "a", "d", "c"], merge=["numbers", "lower"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper", "numbers_lower"])
        self.assertEqual(merged.shape, (3, 20))
        self.assertEqual(merged[2, 9], 30.)

        merged = J(upper=["C", "B", "D"], numbers=["4", "2", "1", "7", "3"], lower=[
                   "e", "a", "d", "c"], merge=["numbers", "lower"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper", "numbers_lower"])
        self.assertEqual(merged.shape, (3, 20))
        self.assertEqual(merged[2, 7], 32.1)

        merged = J(upper=["C", "B", "D"], numbers=["4", "2", "1", "7", "3"], lower=[
                   "e", "a", "d", "c"], merge=["lower", "numbers"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper", "lower_numbers"])
        self.assertEqual(merged.shape, (3, 20))
        self.assertEqual(merged[2, 7], 30.)

        merged = J(numbers=["4", "2", "1", "7", "3"], lower=[
                   "e", "a", "d", "c"], upper=["C", "B", "D"], merge=["lower", "numbers"], order=["lower_numbers", "upper"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["lower_numbers", "upper"])
        self.assertEqual(merged.shape, (20, 3))
        self.assertEqual(merged[7, 2], 30.)
