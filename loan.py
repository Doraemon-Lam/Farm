
# loan.py

class LoanManager:
    def __init__(self, initial_debt=30000, credit_score=100):
        self.total_debt = initial_debt  # 总债务
        self.credit_score = credit_score  # 信用分 (0-100)
        self.base_monthly_payment = 3000  # 每月基础还款额
        self.interest_rate_overdue = 0.05  # 逾期罚息率 (5% on the overdue amount)
        self.repayment_day = 28  # 每月还款日

    @property
    def max_loan_amount(self):
        # 最大可贷金额与信用分挂钩
        # 信用分100时可贷50000，信用分0时可贷1000
        return 1000 + (self.credit_score / 100) * 49000

    def borrow_money(self, amount):
        """
        借款功能。
        - 检查是否超过最大可贷金额。
        - 借款成功后，金额加入总债务，并略微降低信用分。
        """
        if amount <= 0:
            return False, "借款金额必须为正数。"
        
        if amount > self.max_loan_amount:
            return False, f"你的信用额度不足。当前最大可贷金额为 ￥{self.max_loan_amount:.2f}。"

        self.total_debt += amount
        self.credit_score = max(0, self.credit_score - 5) # 每次借款信用分降低5点
        return True, f"成功借款 ￥{amount:.2f}。当前总债务为 ￥{self.total_debt:.2f}。"

    def handle_repayment(self, funds_available):
        """
        处理每月还款。
        - 计算当月应还金额。
        - 根据玩家资金情况处理还款、部分还款或逾期。
        """
        if self.total_debt <= 0:
            return "no_debt", 0, "您已还清所有债务！"

        # 应还金额为基础还款额和剩余债务中的较小者
        due_amount = min(self.base_monthly_payment, self.total_debt)
        
        if funds_available >= due_amount:
            # 全额还款
            self.total_debt -= due_amount
            self.credit_score = min(100, self.credit_score + 2) # 按时还款，信用分增加
            return "paid_full", due_amount, f"成功还款 ￥{due_amount:.2f}。剩余债务: ￥{self.total_debt:.2f}。"
        
        elif funds_available > 0:
            # 部分还款
            paid_amount = funds_available
            remaining_due = due_amount - paid_amount
            
            self.total_debt -= paid_amount
            overdue_penalty = remaining_due * self.interest_rate_overdue
            self.total_debt += overdue_penalty # 罚息计入总债务
            
            self.credit_score = max(0, self.credit_score - 10) # 部分还款，信用分下降
            return "paid_partial", paid_amount, (
                f"资金不足！仅还款 ￥{paid_amount:.2f}。"
                f"剩余未还 ￥{remaining_due:.2f} 已产生 ￥{overdue_penalty:.2f} 的罚息并计入总债务。"
            )
        else:
            # 完全逾期
            overdue_penalty = due_amount * self.interest_rate_overdue
            self.total_debt += overdue_penalty # 罚息计入总债务
            self.credit_score = max(0, self.credit_score - 15) # 完全逾期，信用分大幅下降
            return "overdue", 0, (
                f"本月未能还款！应还金额 ￥{due_amount:.2f} 已产生 ￥{overdue_penalty:.2f} 的罚息并计入总债务。"
            )

    def get_status(self):
        """返回当前贷款状态的字符串"""
        if self.total_debt <= 0:
            return "无债务"
        return f"总债务: ￥{self.total_debt:.2f} | 信用分: {self.credit_score} | 最大可贷: ￥{self.max_loan_amount:.2f}"

