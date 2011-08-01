import class_document
import customers
import dateentry
import dbconfig
import decimalentry
import helpers
import numberentry
import subjects
from amirconfig import config
from database import Subject
from database import Customers

import gtk

type_names = (
    # 0 id, 1 name
    (0 , 'Get From Customer'      ),
    (1 , 'Pay To Customer'        ),
    (2 , 'Bank To Bank'           ),
    (3 , 'Fund To Bank'           ),
    (4 , 'Bank To Fund'           ),
    (5 , 'Bank Wage'              ),
    (6 , 'havale taraf hesab'     ),
    (7 , 'Padakhte naghdi az bank'),
    (8 , 'Investment'             ),
    (9 , 'Cost'                   ),
    (10, 'Income'                 ),
    (11, 'Removel'                ),
)

type_configs = {
    #0 non cash
    #1 discount
    #2 spend_cheque
    #3 from is subject?
    #4 to   is subject?
    #5 from key
    #6 to   key
    #    0    , 1    , 2    , 3   , 4   , 5   , 6
    0:  (True , True , False, False, True , None, None),
    1:  (True , False, True , True , True , None, None),
    2:  (True , False, False, True , True , None, None),
    3:  (False, False, False, True , True , None, None),
    4:  (True , False, False, True , True , None, None),
    5:  (False, False, False, True , True , None, None),
    6:  (False, False, False, True , True , None, None),
    7:  (False, False, False, True , True , None, None),
    8:  (True , False, True , True , True , None, None),
    9:  (True , False, True , True , True , None, None),
    10: (True , False, False, True , True , None, None),
    11: (True , False, True , True , True , None, None),
}

class AutomaticAccounting:
    def __init__(self):
        # Chosen Type
        self.type_index = None
        
        self.builder = helpers.get_builder('automaticaccounting')
        self.builder.connect_signals(self)

        # Date entry
        date_box = self.builder.get_object('date-box')
        self.date_entry = dateentry.DateEntry()
        date_box.pack_start(self.date_entry, False, False)

        # type combo
        type_combo = self.builder.get_object('select-type')
        model = gtk.ListStore(str, str)
        type_combo.set_model(model)

        cell = gtk.CellRendererText()
        cell.set_visible(False)
        type_combo.pack_start(cell)
        type_combo.add_attribute(cell, 'text', 0)

        cell = gtk.CellRendererText()
        type_combo.pack_start(cell)
        type_combo.add_attribute(cell, 'text', 1)

        for item in type_names:
            iter = model.append()
            model.set(iter, 0, item[0], 1, item[1])

        # payment table
        table = self.builder.get_object('payment-table')

        self.cash_payment_entry = decimalentry.DecimalEntry()
        self.cash_payment_entry.connect('changed', self.on_cash_payment_entry_change)
        table.attach(self.cash_payment_entry, 1, 2, 0, 1)

        self.discount_entry = decimalentry.DecimalEntry()
        self.discount_entry.connect('changed', self.on_discount_entry_change)
        table.attach(self.discount_entry, 1, 2, 3, 4)

        # names table
        table = self.builder.get_object('names-table')

        self.from_entry = numberentry.NumberEntry()
        self.from_entry.set_sensitive(False)
        self.from_entry.connect('changed', self.on_from_entry_changed)
        table.attach(self.from_entry, 1, 2, 0, 1)

        self.to_entry = numberentry.NumberEntry()
        self.to_entry.set_sensitive(False)
        self.to_entry.connect('changed', self.on_to_entry_changed)
        table.attach(self.to_entry, 1, 2, 1, 2)

        self.total_credit_entry = decimalentry.DecimalEntry()
        self.total_credit_entry.connect('changed', self.on_total_credit_entry_change)
        table.attach(self.total_credit_entry, 1, 2, 2, 3)

        # choose first type
        type_combo.set_active(0)

    def on_type_change(self, combo):
        iter =  combo.get_active_iter()

        if iter == None:
            return
        
        model = combo.get_model()
        index = model.get(iter, 0)[0]
        self.type_index = int(index)
        
        save_button = self.builder.get_object('save-button')
        save_button.set_sensitive(False)
        
        non_cash, discount, spend_cheque = type_configs[self.type_index][:3]

        self.builder.get_object('discount-button').set_sensitive(discount)
        self.discount_entry.set_sensitive(discount)
        
        self.builder.get_object('list-cheque-button').set_sensitive(spend_cheque)
        self.builder.get_object('spend-cheque-label').set_sensitive(spend_cheque)

        self.builder.get_object('non-cash-payment-label').set_sensitive(non_cash)
        self.builder.get_object('non-cash-payment-button').set_sensitive(non_cash)

        self.cash_payment_entry.set_sensitive((non_cash or spend_cheque))

        self.from_entry.set_text("")
        self.to_entry.set_text("")
        self.cash_payment_entry.set_text('0.0')
        self.total_credit_entry.set_text('0.0')
        self.discount_entry.set_text('0.0')

    def on_from_clicked(self, button):
        index  = self.type_index
        entry  = self.from_entry
        dbconf = dbconfig.dbConfig()

        if type_configs[self.type_index][3]:
            sub = subjects.Subjects()
            sub.connect('subject-selected',
                        self.on_subject_selected,
                        entry)
        else:
            cust = customers.Customer()
            cust.connect('customer-selected',
                         self.on_customer_selected,
                         entry)
            cust.viewCustomers(True)

    def on_to_clicked(self, button):
        entry = self.to_entry
        dbconf = dbconfig.dbConfig()

        if type_configs[self.type_index][4]:
            if type_configs[self.type_index] == None:
                sub = subjects.Subjects()
            else:
                sub = subjects.Subjects()
            sub.connect('subject-selected',
                        self.on_subject_selected,
                        entry)
        else:
            cust = customers.Customer()
            cust.connect('customer-selected',
                         self.on_customer_selected,
                         entry)
            cust.viewCustomers(True)

    def on_total_credit_entry_change(self, entry):
        if not (type_configs[0] or type_configs[2]):
            self.cash_payment_entry.set_text(entry.get_text())
        self.on_cash_payment_entry_change(None)

    def on_discount_entry_change(self, entry):
        self.on_cash_payment_entry_change(None)

    def on_discount_clicked(self, button):
        dialog = gtk.Dialog("My dialog",
                            self.builder.get_object('general'),
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK)
                           )
        adj = gtk.Adjustment(0, 0, 100, 1, 1)
        spin = gtk.SpinButton(adj)

        hbox = gtk.HBox()
        hbox.pack_start(spin)
        hbox.pack_start(gtk.Label(' % '), False, False)
        hbox.show_all()

        dialog.vbox.pack_start(hbox, False, False)

        result = dialog.run()
        if result == gtk.RESPONSE_OK:
            val = spin.get_value()
            total = self.total_credit_entry.get_float()
            discount = (val*total)/100
            self.discount_entry.set_text(str(discount))

        dialog.destroy()

    def on_cash_payment_entry_change(self, entry):
        val1 = self.cash_payment_entry.get_float()
        val2 = float(self.builder.get_object('non-cash-payment-label').get_text())

        discount = self.discount_entry.get_float()

        paid = val1+val2+discount
        paid_label = self.builder.get_object('paid')
        paid_label.set_text(str(paid))

        total = self.total_credit_entry.get_float()
        r = total - (paid)
        mod = self.builder.get_object('mod')
        mod.set_text(str(r))

        self.check_save_button()

    def on_subject_selected(self, subject, id, code, name, entry):
        query = config.db.session.query(Subject).select_from(Subject)
        query = query.filter(Subject.code == code)
        if query.first().parent_id == 0:
            print 'Can not select it'
            return

        entry.set_text(str(code))
        subject.window.destroy()

    def on_customer_selected(self, customer, id, code, entry):
        entry.set_text(str(code))
        customer.window.destroy()

    def on_from_entry_changed(self, entry):
        self.check_save_button()

    def on_to_entry_changed(self, entry):
        self.check_save_button()

    def check_save_button(self):
        save_button = self.builder.get_object('save-button')
        save_button.set_sensitive(False)

        if self.from_entry.get_text_length() == 0: # TODO: and exists
            return

        if self.to_entry.get_text_length() == 0 :  # TODO: and exists
            return

        if self.total_credit_entry.get_float() == 0:
            return

        mod = self.builder.get_object('mod')
        if float(mod.get_text()) != 0:
            return

        save_button.set_sensitive(True)

    def on_save_button_clicked(self, button):
        result = {}
        result['type']                  = self.type_index
        result['total_value']           = self.total_credit_entry.get_float()
        result['cash_payment']          = self.cash_payment_entry.get_float()
        result['non_cash_payment']      = self.builder.get_object('non-cash-payment-label').get_text()
        result['spend_cheque']          = self.builder.get_object('spend-cheque-label').get_text()
        result['discount']              = self.discount_entry.get_float()
        result['non-cash-payment-info'] = None # TODO: = non cash payment infos
        result['spend-cheque-info']     = None # TODO = spent cheque infos
        result['desc']                  = self.builder.get_object('desc').get_text()

        result['from'] = self.from_entry.get_text()
        if type_configs[self.type_index][3]:
            result['from'] = config.db.session.query(Subject).select_from(Subject).filter(Subject.code == result['from']).first().id
        else:
            result['from'] = config.db.session.query(Customers).select_from(Subject).filter(Customers.custCode == result['from']).first().custId

        result['to']   = self.to_entry.get_text()
        if type_configs[self.type_index][4]:
            result['to']   = config.db.session.query(Subject).select_from(Subject).filter(Subject.code == result['to'  ]).first().id
        else:
            result['to'] = config.db.session.query(Customers).select_from(Subject).filter(Customers.custCode == result['to']).first().custId

        for i in result:
            print i, ' => ', result[i]
        print 'END'

        document = class_document.Document()
        document.add_notebook(result['from'],  result['total_value'], result['desc'])
        document.add_notebook(result['to'], -result['total_value'], result['desc'])
        if result['discount']:
            document.add_notebook(result['to'], -result['discount']   , result['desc'])
        print 'Result : ',document.save()

        self.on_destroy(self.builder.get_object('general'))

    def on_destroy(self, window):
        window.destroy()

    def run(self, parent=None):
        win  = self.builder.get_object('general')
        win.connect('destroy', self.on_destroy)

        if parent:
            win.set_transient_for(parent)
        win.set_position(gtk.WIN_POS_CENTER)
        win.set_destroy_with_parent(True)
        win.show_all()

