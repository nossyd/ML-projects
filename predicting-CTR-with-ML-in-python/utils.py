def calc_total_return(tp, r=0.2):
    """Function to calculate total return of ad impression

    Args:
        tp (float): True positive rate of ad impression predictions
        r (float, optional): Return on an ad impression. Defaults to 0.2.
    """

    total_return = tp * r

    return total_return


def calc_total_cost(fp, tp, cost=0.05):
    """Function to calculate total cost of ad impression

    Args:
        fp (float): False positive rate of ad impression predictions
        tp (float): True positive rate of ad impression predictions
        cost (float, optional): Cost of ad impression. Defaults to 0.05.
    """

    total_cost = (fp + tp) * cost

    return total_cost


def calc_roi(total_return, total_cost):
    """Function to calculate return on investment of ad impression

    Args:
        fp (float): False positive rate of ad impression predictions
        tp (float): True positive rate of ad impression predictions
        cost (float, optional): Cost of ad impression. Defaults to 0.05.
    """

    roi = total_return / total_cost

    return roi