#!/usr/bin/python
# coding:utf8

'''
AI火箭营
'''
from numpy import *


def loadSimpData():
    """ 测试数据
    Returns:
        dataArr   feature对应的数据集
        labelArr  feature对应的分类标签
    """
    dataArr = array([[1., 2.1], [2., 1.1], [1.3, 1.], [1., 1.], [2., 1.]])
    labelArr = [1.0, 1.0, -1.0, -1.0, 1.0]
    return dataArr, labelArr


# general function to parse tab -delimited floats
def loadDataSet(fileName):
    # get number of fields
    numFeat = len(open(fileName).readline().split('\t'))
    dataArr = []
    labelArr = []
    fr = open(fileName)
    for line in fr.readlines():
        lineArr = []
        curLine = line.strip().split('\t')
        for i in range(numFeat-1):
            lineArr.append(float(curLine[i]))
        dataArr.append(lineArr)
        labelArr.append(float(curLine[-1]))
    print '中国：',dataArr
    return dataArr, labelArr


def stumpClassify(dataMat, dimen, threshVal, threshIneq):
    """
    树桩，stumpClassify(将数据集，按照feature列的value进行二分切分)

    Args:
        dataMat    数据集矩阵
        dimen      特征列
        threshVal  特征列要比较的值
    Returns:
        retArray 结果集
    """
    # 默认都是1
    retArray = ones((shape(dataMat)[0], 1))
    # dataMat[:, dimen] 表示数据集中所有行的第dimen列的值
    # threshIneq == 'lt'表示修改特征左边的值，gt表示修改右边的值
    # print '-----', threshIneq, dataMat[:, dimen], threshVal
    if threshIneq == 'lt':
        retArray[dataMat[:, dimen] <= threshVal] = -1.0
    else:
        retArray[dataMat[:, dimen] > threshVal] = -1.0
    return retArray


def buildStump(dataArr, labelArr, D):
    """
    buildStump(得到决策树的模型)

    Args:
        dataArr   特征数组
        labelArr  分类标签数组
        D         所有样本的初始权重
    Returns:
        bestStump    最优的分类器模型
        minError     错误率
        bestClasEst  训练后的最优结果
    """
    # 转换数据
    dataMat = mat(dataArr)
    labelMat = mat(labelArr).T
    # m行 n列
    m, n = shape(dataMat)

    # 初始化数据
    numSteps = 10.0
    bestStump = {}
    bestClasEst = mat(zeros((m, 1)))
    # 初始化的最小误差为无穷大
    minError = inf

    # 遍历所有的feature列，将列切分成11份
    for i in range(n):
        rangeMin = dataMat[:, i].min()
        rangeMax = dataMat[:, i].max()
        # print 'rangeMin=%s, rangeMax=%s' % (rangeMin, rangeMax)
        # 计算每一份的元素个数
        stepSize = (rangeMax-rangeMin)/numSteps
        # 例如： 4=(10-1)/2   那么  1-4(-1次)   1(0次)  1+1*4(1次)   1+2*4(2次)
        # 所以： 循环 -1/0/1/2
        '''
                        dim            表示 feature列
                        threshVal      表示树的分界值
                        inequal        表示计算树左右颠倒的错误率的情况
                        weightedError  表示整体结果的错误率
                        bestClasEst    预测的最优结果
        '''
        for j in range(0, int(numSteps)+1):
            # 遍历小于和大于
            for inequal in ['lt', 'gt']:
                # 如果是-1，那么得到rangeMin-stepSize; 如果是numSteps，那么得到rangeMax
                threshVal = (rangeMin + float(j) * stepSize)
                # 对单层决策树进行简单分类，得到预测的分类值
                predictedVals = stumpClassify(dataMat, i, threshVal, inequal)
                # print predictedVals
                errArr = mat(ones((m, 1)))
                # 正确为0，错误为1
                errArr[predictedVals == labelMat] = 0
                # 计算 平均每个特征的概率0.2*错误概率的总和为多少，就知道错误率多高
                # 例如： 一个都没错，那么错误率= 0.2*0=0 ， 5个都错，那么错误率= 0.2*5=1， 只错3个，那么错误率= 0.2*3=0.6
                weightedError = D.T*errArr

                print "split: dim %d, thresh %.2f, thresh ineqal: %s, the weighted error is %.3f" % \
                      (i, threshVal, inequal, weightedError)
                if weightedError < minError:
                    minError = weightedError
                    bestClasEst = predictedVals.copy()
                    bestStump['dim'] = i
                    bestStump['thresh'] = threshVal
                    bestStump['ineq'] = inequal

    # bestStump 表示分类器的结果，在第几个列上，用大于／小于比较，阈值是多少
    return bestStump, minError, bestClasEst


def adaBoostTrainDS(dataArr, labelArr, numIt=40):
    """

    Args:
        dataArr   特征数据
        labelArr  分类数据
        numIt     迭代次数
    Returns:
        weakClassArr  弱分类器集合
        aggClassEst   预测的分类结果值
    """
    weakClassArr = []
    m = shape(dataArr)[0]
    # 初始化样本特征权重 D，平均分为m份，每个1/m
    D = mat(ones((m, 1))/m)
    aggClassEst = mat(zeros((m, 1)))

    for i in range(numIt):

        # 构建决策树桩
        bestStump, error, classEst = buildStump(dataArr, labelArr, D)


        # 计算每个分类器的 alpha 权重值
        alpha = float(0.5*log((1.0-error)/max(error, 1e-16)))
        bestStump['alpha'] = alpha

        # 保存树桩参数
        weakClassArr.append(bestStump)

        print "alpha=%s, classEst=%s, bestStump=%s, error=%s " % \
              (alpha, classEst.T, bestStump, error)

        # 分类正确：乘积为1，求e的-alpha次方
        # 分类错误：乘积为-1，求e的alpha次方
        expon = multiply(-1*alpha*mat(labelArr).T, classEst)
        print '\n'
        print 'labelArr=', labelArr
        print 'classEst=', classEst.T
        print '\n'
        print '乘积: ', multiply(mat(labelArr).T, classEst).T

        print '预测expon=', expon.T
        # 计算e的expon次方，然后计算得到一个综合的概率
        # 结果发现： 判断错误的样本，样本权重D会变大。
        D = multiply(D, exp(expon))
        D = D/D.sum()
        print "D: ", D.T
        print '\n'

        # 预测的分类结果，在上一轮结果的基础上，进行加和操作
        print '当前的分类结果：', alpha*classEst.T
        aggClassEst += alpha*classEst

        print "累积的分类结果aggClassEst: ", aggClassEst.T
        # sign 判断正为1， 0为0， 负为-1，通过最终加和的权重，判断符号。
        # 结果为：错误的样本标签集合
        aggErrors = multiply(sign(aggClassEst) != mat(labelArr).T, ones((m, 1)))
        errorRate = aggErrors.sum()/m

        print "total error=%s " % (errorRate)
        if errorRate == 0.0:
            break
    return weakClassArr, aggClassEst


def adaClassify(datToClass, classifierArr):
    # do stuff similar to last aggClassEst in adaBoostTrainDS
    dataMat = mat(datToClass)
    m = shape(dataMat)[0]
    aggClassEst = mat(zeros((m, 1)))

    # 循环 多个分类器
    for i in range(len(classifierArr)):
        # 前提： 我们已经知道了最佳的分类器的实例
        # 通过分类器来核算每一次的分类结果，然后通过alpha*每一次的结果 得到最后的权重加和的值。
        classEst = stumpClassify(dataMat, classifierArr[i]['dim'], classifierArr[i]['thresh'], classifierArr[i]['ineq'])
        aggClassEst += classifierArr[i]['alpha']*classEst
        # print aggClassEst
    return sign(aggClassEst)


def plotROC(predStrengths, classLabels):
    """plotROC(打印ROC曲线，并计算AUC的面积大小)

    Args:
        predStrengths  最终预测结果的权重值
        classLabels    原始数据的分类结果集
    """
    print 'predStrengths=', predStrengths
    print 'classLabels=', classLabels

    import matplotlib.pyplot as plt
    # variable to calculate AUC
    ySum = 0.0
    # 对正样本的进行求和
    numPosClas = sum(array(classLabels)==1.0)
    # 正样本的概率
    yStep = 1/float(numPosClas)
    # 负样本的概率
    xStep = 1/float(len(classLabels)-numPosClas)
    # argsort函数返回的是数组值从小到大的索引值
    # get sorted index, it's reverse
    sortedIndicies = predStrengths.argsort()
    # 测试结果是否是从小到大排列
    print 'sortedIndicies=', sortedIndicies, predStrengths[0, 176], predStrengths.min(), predStrengths[0, 293], predStrengths.max()

    # 开始创建模版对象
    fig = plt.figure()
    fig.clf()
    ax = plt.subplot(111)
    # cursor光标值
    cur = (1.0, 1.0)
    # loop through all the values, drawing a line segment at each point
    for index in sortedIndicies.tolist()[0]:
        if classLabels[index] == 1.0:
            delX = 0
            delY = yStep
        else:
            delX = xStep
            delY = 0
            ySum += cur[1]
        # draw line from cur to (cur[0]-delX, cur[1]-delY)
        # 画点连线 (x1, x2, y1, y2)
        print cur[0], cur[0]-delX, cur[1], cur[1]-delY
        ax.plot([cur[0], cur[0]-delX], [cur[1], cur[1]-delY], c='b')
        cur = (cur[0]-delX, cur[1]-delY)
    # 画对角的虚线线
    ax.plot([0, 1], [0, 1], 'b--')
    plt.xlabel('False positive rate')
    plt.ylabel('True positive rate')
    plt.title('ROC curve for AdaBoost horse colic detection system')
    # 设置画图的范围区间 (x1, x2, y1, y2)
    ax.axis([0, 1, 0, 1])
    plt.show()
    '''
    参考说明：http://blog.csdn.net/wenyusuran/article/details/39056013
    为了计算 AUC ，我们需要对多个小矩形的面积进行累加。
    这些小矩形的宽度是xStep，因此可以先对所有矩形的高度进行累加，最后再乘以xStep得到其总面积。
    所有高度的和(ySum)随着x轴的每次移动而渐次增加。
    '''
    print "the Area Under the Curve is: ", ySum*xStep


if __name__ == "__main__":
    # # 我们要将5个点进行分类
    dataArr, labelArr = loadSimpData()
    print 'dataArr', dataArr, 'labelArr', labelArr

    # # D表示最初值，对1进行均分为5份，平均每一个初始的概率都为0.2
    # # D的目的是为了计算错误率： weightedError = D.T*errArr
    D = mat(ones((5, 1))/5)
    print 'D=', D.T

    bestStump, minError, bestClasEst = buildStump(dataArr, labelArr, D)
    print 'bestStump=', bestStump
    print 'minError=', minError
    print 'bestClasEst=', bestClasEst.T

    # # 分类器：weakClassArr
    # # 历史累计的分类结果集
    weakClassArr, aggClassEst = adaBoostTrainDS(dataArr, labelArr, 9)
    print '\nweakClassArr=', weakClassArr, '\naggClassEst=', aggClassEst.T

    # """
    # 发现:
    # 分类的权重值：最大的值，为alpha的加和，最小值为-最大值
    # 特征的权重值：如果一个值误判的几率越小，那么D的特征权重越少
    # """

    # # 测试数据的分类结果, 观测：aggClassEst分类的最终权重
    print adaClassify([0, 0], weakClassArr).T
    print adaClassify([[5, 5], [0, 0]], weakClassArr).T

    # 马疝病数据集
    # 训练集合
    dataArr, labelArr = loadDataSet("/Users/zzh/run/ml/mlp/input/7.AdaBoost/horseColicTraining2.txt")
    weakClassArr, aggClassEst = adaBoostTrainDS(dataArr, labelArr, 40)
    print weakClassArr, '\n-----\n', aggClassEst.T
    # 计算ROC下面的AUC的面积大小
    plotROC(aggClassEst.T, labelArr)
    # 测试集合
    dataArrTest, labelArrTest = loadDataSet("/Users/zzh/run/ml/mlp/input/7.AdaBoost/horseColicTest2.txt")
    m = shape(dataArrTest)[0]
    predicting10 = adaClassify(dataArrTest, weakClassArr)
    errArr = mat(ones((m, 1)))
    # 测试：计算总样本数，错误样本数，错误率
    print m, errArr[predicting10 != mat(labelArrTest).T].sum(), errArr[predicting10 != mat(labelArrTest).T].sum()/m
