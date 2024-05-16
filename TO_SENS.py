import numpy as np
import matplotlib.pyplot as plt


class sensitivity:
    def __init__(self, score_matrix, weights_arr, option_names, criteria_names):
        self.n_criteria = score_matrix.shape[0]
        self.n_options = score_matrix.shape[1]
        self.scores = score_matrix
        self.weights = weights_arr

        self.opt_names = option_names
        self.crit_names = criteria_names


    def weighted_score(self, option, weights):
        ws = np.sum(weights * option)
        return ws

    def perform_sensitivity_per_crit(self, criterion_pChanges, n_points: int = 10):
        'initial weights'
        initial_weights = self.weights
        for i in range(self.n_criteria):
            'initialise the final weights'
            final_weights = np.zeros((self.n_criteria, n_points))

            'get the ith % change and weight'
            percentage_change = criterion_pChanges[i]
            current_weight = initial_weights[i]

            'assign array of multiplied w_i to final weights'
            main_mult_range = np.linspace(1-percentage_change/100, 1+percentage_change/100, n_points)
            remaining_weights = initial_weights[initial_weights!=current_weight]
            changed_main_w = main_mult_range * current_weight
            final_weights[i,:] = changed_main_w

            'assign array of multiplied w_k k!=i to final weights'
            remaining_mult_range = (1-changed_main_w)/(np.sum(remaining_weights))
            remaining_w = remaining_weights[:,np.newaxis] * remaining_mult_range
            final_weights[np.where(self.weights != current_weight),:] = remaining_w

            'matmul over criteria'
            weighted_scores = np.einsum('ij, jk->ik', self.scores.T, final_weights)
            #print(weighted_scores[:,-1])
            self.plot_sensitivity(x_axis=main_mult_range-1, weighted_scores=weighted_scores, idx=i)
        return

    def plot_sensitivity(self, idx, x_axis, weighted_scores):
        plt.figure(figsize=(5.5,5))
        for k in range(weighted_scores.shape[0]):
            plt.plot(x_axis, weighted_scores[k,:], label = f'{self.opt_names[k]}', linewidth=1)
        plt.title(f'Criterion: {self.crit_names[idx]}')
        plt.xlabel('relative change', fontsize=12)
        plt.ylabel('weighted score', fontsize=12)
        plt.legend()
        plt.show()


def sens_structures():
    criterion_weights = np.array([.5, .2, .3])

    scores = np.array([[3, 2, 1, ],
                       [4, 3, 2, ],
                       [5, 1, 2, ]])



    criterion_changes = np.array([100, 100, 100])

    design_option_names = ['truss+tower', 'truss+platform', 'branching', ]
    criteria_names = ['cost', 'maintenance', 'complexity']

    TEST = sensitivity(score_matrix=scores, weights_arr=criterion_weights, option_names=design_option_names,
                       criteria_names=criteria_names)
    TEST.perform_sensitivity_per_crit(criterion_pChanges=criterion_changes)


    
def sens_afc():
    criterion_weights = np.array([0.3, 0.3, 0.15, 0.15, 0.1])

    scores = np.array([[2, 2, 5, 5, 3 ,5, 5],
                    [4, 1, 1, 5 ,2, 1, 4],
                    [3, 4, 4, 3, 5, 2, 3 ],
                    [4, 3, 2, 4, 3, 1, 4],
                    [3, 4, 5, 5, 5, 2 ,1]])

    criterion_changes = np.array([50, 50, 50, 50, 50])
    design_option_names = ['single rotor', 'full sturcture', 'fixed HLD', 'retractable HLD', 'no HLD', 'fixed softwing', 'retractable softwing']
    criteria_names = ['vertical flow displacement', 'meteorologica versatility', 'reliability/complexity', 'structural resilience', 'innovation maturity']

    TEST = sensitivity(score_matrix=scores, weights_arr=criterion_weights, option_names=design_option_names, criteria_names=criteria_names)
    TEST.perform_sensitivity_per_crit(criterion_pChanges=criterion_changes)




if __name__ == '__main__':
    sens_afc()
