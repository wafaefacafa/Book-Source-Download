import re

class BookClassifier:
    """
    书名语义分析器 (Semantic Book Classifier)
    根据书名关键词和命名模式推测题材，并推荐最合适的书源优先级。
    """
    def __init__(self):
        # 定义分类关键词库
        self.genre_keywords = {
            'fan_fiction': {
                'tags': ['同人', '综漫', '诸天'],
                'keywords': [
                    '诸天', '综漫', '斗罗', '宇智波', '海贼', '火影', '万界', '穿越从', '原神', 
                    '假面骑士', '奥特曼', '柯南', '龙珠', '死神', '漫威', 'DC', '神奇宝贝'
                ],
                'patterns': [r'.*从.*开始', r'人在.*', r'开局.*同人']
            },
            'light_novel': {
                'tags': ['轻小说', '二次元', '变身'],
                'keywords': [
                    '变身', '女装', '恶龙', '魔王', '勇者', '转生', '重生为', '日常', '恋爱', 
                    '她们', '大小姐', '圣女', '公主', '病娇', '美少女', '学姐', '妹妹'
                ],
                'patterns': [r'.*的日子里', r'我，.*', r'关于.*这件事']
            },
            'system_flow': {
                'tags': ['系统流', '无敌流'],
                'keywords': [
                    '系统', '无敌', '签到', '开局', '满级', '神豪', '提取', '奖励', '无限', '进化', '模板'
                ],
                'patterns': [r'开局.*', r'我有.*', r'从.*开始打卡']
            },
            'xianxia_fantasy': {
                'tags': ['仙侠', '玄幻', '长生'],
                'keywords': [
                    '丹神', '剑圣', '气运', '长生', '炼气', '筑基', '金丹', '元神', '圣体', '荒古', 
                    '大帝', '至尊', '遮天', '完美', '凡人', '修仙', '证道', '飞升'
                ],
                'patterns': [r'.*之主', r'最强.*']
            },
            'urban_romance': {
                'tags': ['都市', '神医', '战神'],
                'keywords': [
                    '神医', '战神', '赘婿', '龙帅', '枭雄', '兵王', '神算', '天师', '鉴宝', '总裁', '娇妻'
                ],
                'patterns': [r'镇世.*', r'战神.*', r'第一.*']
            }
        }

        # 定义书源优先级建议
        # group_priority: 推荐的书源分组关键字
        # name_priority: 推荐的特定书源名称关键字
        self.source_recommendations = {
            'light_novel': {
                'group': ['ACG', '轻小说'],
                'names': ['菠萝包', '刺猬猫', 'SF', '轻书架'],
                'reason': '包含二次元相关关键词，优先检索垂直次元站。'
            },
            'fan_fiction': {
                'group': ['同人'],
                'names': ['刺猬猫', '69书吧', '番茄'],
                'reason': '同人作品在特定社区或大型综合源更全。'
            },
            'xianxia_fantasy': {
                'group': ['原创', '玄幻'],
                'names': ['69书吧', '笔趣阁', '纵横', '17K'],
                'reason': '传统玄幻仙侠建议从老牌综合源检索。'
            },
            'default': {
                'group': ['优'],
                'names': ['69书吧', '新笔趣阁'],
                'reason': '未触碰特定模式，按通用高质量源排序。'
            }
        }

    def analyze(self, title):
        """
        分析书名并返回分类报告
        """
        results = {
            'detected_genres': [],
            'hit_keywords': [],
            'recommendation': self.source_recommendations['default'],
            'confidence': 0.0
        }

        max_hits = 0
        primary_genre = None

        for genre, data in self.genre_keywords.items():
            hits = 0
            # 关键词匹配
            for kw in data['keywords']:
                if kw in title:
                    hits += 1
                    results['hit_keywords'].append(kw)
            
            # 正则模式匹配
            for pattern in data['patterns']:
                if re.match(pattern, title):
                    hits += 2 # 模式匹配权重更高
                    results['hit_keywords'].append(f"Pattern:{pattern}")

            if hits > 0:
                results['detected_genres'].extend(data['tags'])
                if hits > max_hits:
                    max_hits = hits
                    primary_genre = genre

        # 计算置信度 (简单模型)
        results['confidence'] = min(1.0, max_hits / 5.0)

        # 更新建议
        if primary_genre and primary_genre in self.source_recommendations:
            results['recommendation'] = self.source_recommendations[primary_genre]
        elif primary_genre == 'system_flow': # 系统流通常混在其他流派中
            results['recommendation'] = self.source_recommendations['xianxia_fantasy']

        return results

if __name__ == "__main__":
    # 测试代码
    classifier = BookClassifier()
    test_titles = [
        "闭嘴恶龙",
        "人在火影：开局签到写轮眼",
        "长生从炼气开始",
        "都市之战神赘婿",
        "我，魔王，变身美少女在转生后的日子里"
    ]
    
    for t in test_titles:
        report = classifier.analyze(t)
        print(f"书名: {t}")
        print(f"标签: {report['detected_genres']}")
        print(f"推荐理由: {report['recommendation']['reason']}")
        print("-" * 30)
