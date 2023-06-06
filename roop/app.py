import numpy
import cv2
from insightface.utils import face_align
from insightface.model_zoo import SCRFD, ArcFaceONNX

class SCRFD_Child(SCRFD):
    def filter_max_num(self, det, kpss, img_shape, max_num, metric):
        # caculate the area of candidate boxes.
        area = (det[:, 2] - det[:, 0]) * (det[:, 3] - det[:, 1])
        # caculate the offsets of candidate box from the center of image.
        img_center = img_shape[0] // 2, img_shape[1] // 2
        offsets = numpy.vstack([
            (det[:, 0] + det[:, 2]) / 2 - img_center[1],
            (det[:, 1] + det[:, 3]) / 2 - img_center[0]
        ])
        offset_dist_squared = numpy.sum(numpy.power(offsets, 2.0), 0)
        # according to different mertrics, caculate the priority value of candidate boxes 
        if metric=='max':
            values = area
        else:
            values = area - offset_dist_squared * 2.0  # some extra weight on the centering
        # sort the candidate boxes in desending order based on their priority values and keep the top 'max_num' boxes.
        top_index = numpy.argsort(values)[::-1]
        top_index = top_index[0:max_num]
        det = det[top_index, :]
        if kpss is not None:
            kpss = kpss[top_index, :]
        return det, kpss
    
    # add threshold for SCRFD
    def detect(self, img, input_size = None, thresh=None, max_num=0, metric='default'):
        assert input_size is not None or self.input_size is not None
        input_size = self.input_size if input_size is None else input_size
        im_ratio = float(img.shape[0]) / img.shape[1]
        model_ratio = float(input_size[1]) / input_size[0]
        if im_ratio>model_ratio:
            new_height = input_size[1]
            new_width = int(new_height / im_ratio)
        else:
            new_width = input_size[0]
            new_height = int(new_width * im_ratio)
        det_scale = float(new_height) / img.shape[0]
        resized_img = cv2.resize(img, (new_width, new_height))
        det_img = numpy.zeros( (input_size[1], input_size[0], 3), dtype=numpy.uint8 )
        det_img[:new_height, :new_width, :] = resized_img
        # add threshold for SCRFD
        det_thresh = thresh if thresh is not None else self.det_thresh
        scores_list, bboxes_list, kpss_list = self.forward(det_img, det_thresh)
        scores = numpy.vstack(scores_list)
        scores_ravel = scores.ravel()
        order = scores_ravel.argsort()[::-1]
        bboxes = numpy.vstack(bboxes_list) / det_scale
        if self.use_kps:
            kpss = numpy.vstack(kpss_list) / det_scale
        pre_det = numpy.hstack((bboxes, scores)).astype(numpy.float32, copy=False)
        pre_det = pre_det[order, :]
        keep = self.nms(pre_det)
        det = pre_det[keep, :]
        if self.use_kps:
            kpss = kpss[order,:,:]
            kpss = kpss[keep,:,:]
        else:
            kpss = None
        if max_num > 0 and det.shape[0] > max_num:
            det, kpss = self.filter_max_num(det, kpss, img.shape, max_num, metric)
        return det, kpss

    # add autodetect for improving the performance.
    def autodetect(self, img, max_num=0, metric='max'):
        # use different input size to detect face, intend to improve the recall rate of detection.
        bboxes_large, kpss_large = self.detect(img, input_size=(640, 640), thresh=0.5)
        bboxes_small, kpss_small = self.detect(img, input_size=(128, 128), thresh=0.5)
        
        # Merging detection results from two different scales.
        bboxes_merged = numpy.concatenate([bboxes_large, bboxes_small], axis=0)
        kpss_merged = numpy.concatenate([kpss_large, kpss_small], axis=0)
        
        # Apply NMS to the merged results to remove overlapping candidate boxes.
        keep = self.nms(bboxes_merged)
        det = bboxes_merged[keep,:]
        kpss = kpss_merged[keep,:]
        
        # if the max_num is specified, fliter the results ,and keep the top-performing candidate box.
        if max_num > 0 and det.shape[0] > max_num:
            det, kpss = self.filter_max_num(det, kpss, img.shape, max_num, metric)
        return det, kpss
    

class ArcFaceONNX_Child(ArcFaceONNX):
    def get(self, img, face):
        aimg = face_align.norm_crop(img, landmark=face, image_size=self.input_size[0])
        embedding = self.get_feat(aimg).flatten()
        return embedding